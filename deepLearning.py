from imdbpie import Imdb
from sklearn.cluster import SpectralCoclustering
import itertools
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import seaborn as sns
import time
import tmdbsimple as tmdb
# import json
# import random
# import requests
# import urllib2
# import wget

api_key = ''
tmdb.API_KEY = api_key
search = tmdb.Search()
imbd_object = Imdb()
imdb = Imdb(anonymize=True)  # to proxy requests

# set the path where you want the scraped folders to be saved
poster_folder = 'posters_final/'
if poster_folder.split('/')[0] not in os.listdir('./'):
    os.mkdir('./' + poster_folder)


def main():
    # print("TMDB: ", get_movie_genres_tmdb("The Sandlot"))
    # print("IMDB: ", get_movie_genres_imdb("The Sandlot"))

    # Only use once, then use the pickle file afterwards
    # pull_top_1000_movies_from_internet()

    top1000_movies = load_top1000_movies_from_pickle()

    allPairs = []
    for movie in top1000_movies:
        allPairs.extend(list2pairs(movie['genre_ids']))

    num_ids = np.unique(allPairs)
    visGrid = np.zeros((len(num_ids), len(num_ids)))
    for p in allPairs:
        visGrid[np.argwhere(num_ids == p[0]),
                np.argwhere(num_ids == p[1])] += 1
        if p[1] != p[0]:
            visGrid[np.argwhere(num_ids == p[1]),
                    np.argwhere(num_ids == p[0])] += 1

    genres_dict = make_genre_dict()

    model = SpectralCoclustering(n_clusters=5)
    model.fit(visGrid)

    fit_data = visGrid[np.argsort(model.row_labels_)]
    fit_data = fit_data[:, np.argsort(model.column_labels_)]

    annot_lookup_sorted = []
    for i in np.argsort(model.row_labels_):
        annot_lookup_sorted.append(genres_dict[num_ids[i]])

    sns.heatmap(fit_data, xticklabels=annot_lookup_sorted,
                yticklabels=annot_lookup_sorted, annot=False)
    plt.title("After biclustering; rearranged to show biclusters")

    plt.show()


def pull_top_1000_movies_from_internet():
    all_movies = tmdb.Movies()
    top1000_movies = []
    print('Pulling movie list, Please wait...')
    for i in range(1, 51):
        if i % 15 == 0:
            time.sleep(7)
        movies_on_this_page = all_movies.popular(page=i)['results']
        top1000_movies.extend(movies_on_this_page)
    len(top1000_movies)
    f3 = open('movie_list.pckl', 'wb')
    pickle.dump(top1000_movies, f3)
    f3.close()
    print('Done')


def load_top1000_movies_from_pickle():
    f3 = open('movie_list.pckl', 'rb')
    top1000_movies = pickle.load(f3)
    f3.close()
    return top1000_movies


# This function just generates all possible pairs of movies
def list2pairs(l):
    # itertools.combinations(l,2) makes all pairs of length 2 from list l.
    pairs = list(itertools.combinations(l, 2))
    # Get the one item pairs, duplicate pairs aren't accounted for by itertools
    for i in l:
        pairs.append([i, i])
    return pairs


def make_genre_dict():
    genres = tmdb.Genres()
    list_of_genres = genres.list()['genres']
    genre_dict = {}
    for i in range(len(list_of_genres)):
        genre_id = list_of_genres[i]['id']
        genre_name = list_of_genres[i]['name']
        genre_dict[genre_id] = genre_name

    return genre_dict


def grab_poster_tmdb(movie):
    response = search.movie(query=movie)
    id = response['results'][0]['id']
    movie = tmdb.Movies(id)
    poster_path = movie.info()['poster_path']
    title = movie.info()['original_title']
    url = 'image.tmdb.org/t/p/original' + poster_path
    title = '_'.join(title.split(' '))
    command = 'wget -O ' + poster_folder + title + '.jpg ' + url
    os.system(command)


def get_movie_id_tmdb(movie):
    response = search.movie(query=movie)
    movie_id = response['results'][0]['id']
    return movie_id


def get_movie_info_tmdb(movie):
    response = search.movie(query=movie)
    id = response['results'][0]['id']
    movie = tmdb.Movies(id)
    info = movie.info()
    return info


def get_movie_genres_imdb(movie):
    imbd_results = imbd_object.search_for_title(movie)
    movie = imbd_object.get_title_by_id(imbd_results[0]['imdb_id'])
    return movie.genres


def get_movie_genres_tmdb(movie):
    response = search.movie(query=movie)
    id = response['results'][0]['id']
    movie = tmdb.Movies(id)
    genres = movie.info()['genres']
    return genres


if __name__ == "__main__":
    main()


# try:
#     search.movie(query=movie) #An API request
# except:
#     try:
#         time.sleep(10) #sleep for a bit, to give API requests a rest.
#         search.movie(query=<i>movie_name</i>) #Make second API request
#     except:
#         print "Failed second attempt, check if there's an error in request"

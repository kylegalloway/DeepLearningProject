import itertools
import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import seaborn as sns
import time
import tmdbsimple as tmdb
import urllib.request

from imdbpie import Imdb
from sklearn.cluster import SpectralCoclustering

api_key = ''
tmdb.API_KEY = api_key

# set the path where you want the scraped folders to be saved
poster_folder = 'posters_final/'
if poster_folder.split('/')[0] not in os.listdir('./'):
    os.mkdir('./' + poster_folder)

search = tmdb.Search()
imbd_object = Imdb(anonymize=True)  # to proxy requests


def make_genre_dict():
    genres = tmdb.Genres()
    list_of_genres = genres.list()['genres']
    genre_dict = {}
    for g in list_of_genres:
        genre_dict[g['id']] = g['name']

    return genre_dict


Genre_ID_to_name = make_genre_dict()


def main():
    # print("TMDB: ".format(get_movie_genres_tmdb("The Sandlot")))
    # print("IMDB: ".format(get_movie_genres_imdb("The Sandlot")))

    # Only use once, then use the pickle file afterwards
    # pull_top_1000_movies_from_internet()
    top1000_movies = load_top1000_movies_from_pickle()

    # make_and_show_heatmap(top1000_movies)
    # cluster_data_and_show_heatmap(top1000_movies)

    # Only use once, then use the pickle file afterwards
    # pull_movies_for_all_unique_genre_pairs_from_internet(top1000_movies)
    movies = load_movies_for_all_unique_genre_pairs_from_pickle()
    unique_movies = remove_duplicates(movies)

    movies_with_overviews = remove_movies_without_overviews(unique_movies)

    # Only use once, then use the pickle file afterwards
    # pull_posters_for_movies_from_internet(unique_movies)
    movies_with_poster = load_posters_for_movies_from_pickle(movies)[0]
    movies_without_poster = load_posters_for_movies_from_pickle(movies)[1]


def remove_duplicates(movies):
    movie_ids = [m['id'] for m in movies]
    movie_ids = np.unique(movie_ids)
    seen_before = []
    no_duplicate_movies = []
    for i in range(len(movies)):
        movie = movies[i]
        id = movie['id']
        if id not in seen_before:
            seen_before.append(id)
            no_duplicate_movies.append(movie)

    return no_duplicate_movies


def remove_movies_without_overviews(movies):
    movies_with_overviews = []
    for m in movies:
        if len(m['overview']) != 0:
            movies_with_overviews.append(m)

    return movies_with_overviews


def make_visgrid(movies):
    allPairs = []
    for movie in movies:
        allPairs.extend(list2pairs(movie['genre_ids']))

    num_ids = np.unique(allPairs)
    visGrid = np.zeros((len(num_ids), len(num_ids)))
    for p in allPairs:
        visGrid[np.argwhere(num_ids == p[0]),
                np.argwhere(num_ids == p[1])] += 1
        if p[1] != p[0]:
            visGrid[np.argwhere(num_ids == p[1]),
                    np.argwhere(num_ids == p[0])] += 1

    return visGrid


def make_and_show_heatmap(movies):
    visgrid = make_visgrid(movies)

    genre_names = []
    for i in range(len(num_ids)):
        genre_names.append(Genre_ID_to_name[num_ids[i]])

    sns.heatmap(visGrid, xticklabels=genre_names, yticklabels=genre_names)
    plt.title("Heatmap of pairings of genres")
    plt.show()


def cluster_data_and_show_heatmap(movies):
    visgrid = make_visgrid(movies)

    model = SpectralCoclustering(n_clusters=5)
    model.fit(visGrid)

    fit_data = visGrid[np.argsort(model.row_labels_)]
    fit_data = fit_data[:, np.argsort(model.column_labels_)]

    sorted_genre_names = []
    for i in np.argsort(model.row_labels_):
        sorted_genre_names.append(Genre_ID_to_name[num_ids[i]])

    sns.heatmap(fit_data, xticklabels=sorted_genre_names,
                yticklabels=sorted_genre_names, annot=False)
    plt.title("After biclustering; rearranged to show biclusters")
    plt.show()


def pull_top_1000_movies_from_internet():
    all_movies = tmdb.Movies()
    top1000_movies = []
    print("Pulling Top 1000 movies from TMBD...")
    for i in range(1, 51):
        if i % 15 == 0:
            time.sleep(7)
        movies_on_this_page = all_movies.popular(page=i)['results']
        top1000_movies.extend(movies_on_this_page)
    len(top1000_movies)
    f = open('movie_list.pckl', 'wb')
    pickle.dump(top1000_movies, f)
    f.close()
    print("Done")


def load_top1000_movies_from_pickle():
    f = open('movie_list.pckl', 'rb')
    top1000_movies = pickle.load(f)
    f.close()
    return top1000_movies


def pull_movies_for_all_unique_genre_pairs_from_internet(movies):
    allPairs = []
    for movie in movies:
        allPairs.extend(list2pairs(movie['genre_ids']))

    num_ids = np.unique(allPairs)
    movies = []
    baseyear = 2017

    done_ids = []
    print("Pulling unique movies from TMBD (total {0})...".format(num_ids))
    for g_id in num_ids:
        baseyear -= 1
        for page in range(1, 6):
            time.sleep(0.5)

            url = 'https://api.themoviedb.org/3/discover/movie?api_key='
            url += api_key
            url += '&language=en-US&sort_by=popularity.desc&year='
            url += str(baseyear)
            url += '&with_genres=' + str(g_id) + '&page=' + str(page)

            data = urllib.request.urlopen(url).read().decode('UTF-8')

            dataDict = json.loads(data)
            movies.extend(dataDict["results"])
        done_ids.append(str(g_id))

    f = open("movies_for_posters.pckl", 'wb')
    pickle.dump(movies, f)
    f.close()
    print("Done")


def load_movies_for_all_unique_genre_pairs_from_pickle():
    f = open("movies_for_posters.pckl", 'rb')
    movies = pickle.load(f)
    f.close()
    return movies


def pull_posters_for_movies_from_internet(movies):
    poster_movies = []
    counter = 0
    movies_no_poster = []
    print("Pulling movie posters from TMBD (total {0})...".format(len(movies)))
    for movie in movies:
        id = movie['id']
        title = movie['title']
        # if counter == 1:
        #     print('Downloaded first. Code is working fine. Please wait...')
        if counter % 300 == 0 and counter != 0:
            print("Done with {0} movies out of {1} total".format(
                counter, len(movies)))
        try:
            print("Grabbing: {0}".format(title))
            grab_poster_tmdb(title)
            print("1st try!")
            poster_movies.append(movie)
        except:
            try:
                time.sleep(7)
                print("2nd try at: {0}".format(title))
                grab_poster_tmdb(title)
                print("Got it 2nd time")
                poster_movies.append(movie)
            except:
                movies_no_poster.append(movie)
                print("Failed to download: {0}".format(title))
        counter += 1

    f = open('poster_movies.pckl', 'wb')
    pickle.dump(poster_movies, f)
    f.close()
    f = open('no_poster_movies.pckl', 'wb')
    pickle.dump(movies_no_poster, f)
    f.close()
    print("Done")


def load_posters_for_movies_from_pickle(movies):
    f = open('poster_movies.pckl', 'rb')
    poster_movies = pickle.load(f)
    f.close()
    f = open('no_poster_movies.pckl', 'rb')
    movies_no_poster = pickle.load(f)
    f.close()
    return (poster_movies, movies_no_poster)


def list2pairs(l):
    # itertools.combinations(l,2) makes all pairs of length 2 from list l.
    pairs = list(itertools.combinations(l, 2))
    # Get the one item pairs, duplicate pairs aren't included by itertools
    for i in l:
        pairs.append([i, i])
    return pairs


def get_movie_id_tmdb(movie):
    response = search.movie(query=movie)
    movie_id = response['results'][0]['id']
    return movie_id


def grab_poster_tmdb(movie):
    movie = tmdb.Movies(get_movie_id_tmdb(movie))
    poster_path = movie.info()['poster_path']
    title = movie.info()['original_title']
    if poster_path:
        url = 'http://image.tmdb.org/t/p/original' + poster_path
        title = '_'.join(title.split(' '))
        output_file = poster_folder + title + '.jpg'
        print("Poster: ".format(title))
        if not os.path.exists(output_file):
            print("Does not exist. Grabbing...")
            urllib.request.urlretrieve(url, filename=output_file)


def get_movie_info_tmdb(movie):
    movie = tmdb.Movies(get_movie_id_tmdb(movie))
    info = movie.info()
    return info


def get_movie_genres_tmdb(movie):
    movie = tmdb.Movies(get_movie_id_tmdb(movie))
    genres = movie.info()['genres']
    return genres


def get_movie_genres_imdb(movie):
    imbd_results = imbd_object.search_for_title(movie)
    movie = imbd_object.get_title_by_id(imbd_results[0]['imdb_id'])
    return movie.genres


if __name__ == "__main__":
    main()

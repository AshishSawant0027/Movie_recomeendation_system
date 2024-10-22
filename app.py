import pickle
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Fetch movie poster and details
def fetch_poster_and_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    data = requests.get(url).json()

    # Fetch poster
    poster_path = data.get('poster_path')
    full_poster_path = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "https://via.placeholder.com/500"

    # Fetch movie details
    title = data.get('title', 'N/A')
    tagline = data.get('tagline', 'No tagline available')  # Tagline added
    release_date = data.get('release_date', 'N/A')
    runtime = data.get('runtime', 'N/A')
    overview = data.get('overview', 'Overview not available')
    genres = ', '.join([genre['name'] for genre in data.get('genres', [])])

    # Revenue and budget for hit/survived status
    revenue = data.get('revenue', 0)
    budget = data.get('budget', 0)
    status = 'Hit' if (revenue - budget) > 0 else 'Survived'

    # Vote average (rating)
    vote_average = round(data.get('vote_average', 0), 1)

    return {
        'poster': full_poster_path,
        'overview': overview,
        'release_date': release_date,
        'runtime': runtime,
        'title': title,
        'tagline': tagline,  # Returning tagline
        'genres': genres,
        'status': status,  # Returning hit/survived status
        'vote_average': vote_average  # Returning vote average (rating)
    }

# Movie recommendation function
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    movie_ids = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        details = fetch_poster_and_details(movie_id)
        recommended_movie_names.append(details['title'])
        recommended_movie_posters.append(details['poster'])
        movie_ids.append(movie_id)

    return recommended_movie_names, recommended_movie_posters, movie_ids


# Load the movie list and similarity matrix
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))


# Home route
@app.route('/', methods=['GET', 'POST'])
def home():
    movie_list = movies['title'].values
    movie_recommendations = None
    selected_movie = None

    # Handling form submission
    if request.method == 'POST':
        selected_movie = request.form.get('selected_movie')
        recommended_movie_names, recommended_movie_posters, movie_ids = recommend(selected_movie)
        movie_recommendations = zip(recommended_movie_names, recommended_movie_posters, movie_ids)

    return render_template('index.html', movie_list=movie_list, movie_recommendations=movie_recommendations,
                           selected_movie=selected_movie)


# Movie details route
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    details = fetch_poster_and_details(movie_id)
    return render_template('movie_detail.html',
                           poster=details['poster'],
                           overview=details['overview'],
                           release_date=details['release_date'],
                           runtime=details['runtime'],
                           title=details['title'],
                           tagline=details['tagline'],  # Passing tagline to the template
                           genres=details['genres'],
                           status=details['status'],  # Passing hit/survived status
                           vote_average=details['vote_average'])  # Passing rating to the template


# New route to handle AJAX request for search suggestions
@app.route('/search', methods=['GET'])
def search_movies():
    query = request.args.get('query', '')
    matching_movies = [movie for movie in movies['title'] if query.lower() in movie.lower()]
    return jsonify(matching_movies)


if __name__ == '__main__':
    app.run(debug=True)

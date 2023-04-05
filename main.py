from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


# ------------------The movie DB--------------------
TMDB_API_KEY = 'b8c2970e6df31be428d8e71e99380ad4'
SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
IMG_BASE_URL = 'https://image.tmdb.org/t/p/w500'

parameters_movie = {
    'api_key': TMDB_API_KEY,
    'query': ''
}

parameters_movie_id = {
    'api_key': TMDB_API_KEY,

}


# -----------------------app---------------------------
app = Flask(__name__)
app.app_context().push()
app.config['SECRET_KEY'] = '8BYkEfBA62O6donzWlSihBXox7C0sKR6b'

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-10-movie-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

Bootstrap(app)


# CREATE TABLE
class MovieModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


@app.route("/")
def home():
    all_movies = db.session.query(MovieModel).order_by('ranking').all()
    return render_template("index.html", movies=all_movies)


class EditForm(FlaskForm):
    review = StringField(label='Your review', validators=[DataRequired()])
    rating = StringField(label='Your rating out of 10(e.g. 7.7)', validators=[DataRequired()])
    ranking = StringField(label='Ranking of the movie in the list', validators=[DataRequired()])
    submit = SubmitField(label='update rating')


@app.route('/edit', methods=["GET", "POST"])
def edit():
    m_id = request.args.get('id')
    selected_movie = MovieModel.query.get(m_id)
    form = EditForm()

    if form.validate_on_submit():
        selected_movie.review = form.review.data
        selected_movie.rating = form.rating.data
        selected_movie.ranking = form.ranking.data
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('edit.html', movie=selected_movie, form=form)


@app.route('/delete')
def delete():

    m_id = request.args.get('id')
    movie_to_delete = MovieModel.query.get(m_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


class AddForm(FlaskForm):
    movie = StringField(label='Movie name', validators=[DataRequired()])
    submit = SubmitField(label='Add')


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddForm()

    if form.validate_on_submit():
        movie = form.movie.data.title()
        parameters_movie['query'] = movie
        response = requests.get(url=SEARCH_URL, params=parameters_movie).json()['results']
        return render_template('select.html', movies=response)

    return render_template('add.html', form=form)


@app.route('/select')
def select():
    movie_id = request.args.get('id')
    movie = requests.get(url=f'https://api.themoviedb.org/3/movie/{str(movie_id)}', params=parameters_movie_id).json()
    poster_path = movie["poster_path"]
    image_url = f'{IMG_BASE_URL}{poster_path}'

    new_movie = MovieModel(
        title=movie['title'],
        img_url=image_url,
        description=movie['overview'],
        year=movie['release_date'].strip('-')[:4],
        rating=movie['vote_average'],
        ranking=10+movie['id'],
        review=movie['tagline']
    )
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)

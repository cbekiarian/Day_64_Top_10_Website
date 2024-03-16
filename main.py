from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,HiddenField
from wtforms.validators import DataRequired
import requests

class Base(DeclarativeBase):
  pass


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap5(app)

# CREATE DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class MovieForm(FlaskForm):
    id = HiddenField()
    rating = StringField('Your Rating Out of 10 e.g 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])

    submit = SubmitField('Done')
class AddMovie(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])

    submit = SubmitField('Add Movie')
# CREATE TABLE
class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String,unique=True, nullable=True)
    year: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String, nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)

with app.app_context():
    db.create_all()
MOVIE_DB_API_KEY = "51330305b8c61fbf67eed6f4b1683243"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1MTMzMDMwNWI4YzYxZmJmNjdlZWQ2ZjRiMTY4MzI0MyIsInN1YiI6IjY1ZjU3MGMzZTAzOWYxMDEzMTAyNWM0YiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.OO65ouiA03ohhb49e5A6RQiWKZBn28SaqT30enbmyuA"
}

SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
INFO_URL = "https://api.themoviedb.org/3/movie"

@app.route("/")
def home():


    all_movies = db.session.execute(db.select(Movies).order_by(Movies.rating)).scalars().all()
    i = len(all_movies)
    print(i)
    j=0
    for movies in all_movies:
        movies.ranking = i -j
        db.session.commit()
        j = j+1

    return render_template("index.html",all_movies=all_movies)

@app.route("/edit",methods=['GET','POST'])
def edit():
    print(request.method)
    form = MovieForm()
    movie_id = request.args.get("id")
    if form.validate_on_submit():
        with app.app_context():
            print (movie_id)
            update_movie = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
            print ( form.rating.data)
            update_movie.rating = form.rating.data
            update_movie.review = form.review.data
            print(form.review.data)
            db.session.commit()
        return redirect(url_for("home"))
    else:
        form =MovieForm()
        movie_id = request.args.get("id")
        print(movie_id)
        with app.app_context():
            movie = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
            print (movie)
        return render_template("edit.html", movie=movie, form = form)

@app.route("/delete",methods=['GET','POST'])
def delete():
    movie_id = request.args.get("id")
    with app.app_context():
        delete_movie = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
        db.session.delete(delete_movie)
        db.session.commit()
        return redirect(url_for("home"))

@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddMovie()

    if form.validate_on_submit():
        possible_movies = requests.get(SEARCH_URL, headers=headers,params={"query": form.title.data} ).json()["results"]
        print(possible_movies)
        return render_template("select.html", possible_movies=possible_movies)
    if request.args.get("id"):
        print(request.args.get("id"))
        possible_movies = requests.get(f"{INFO_URL}/{request.args.get("id")}", headers=headers ).json()
        print(possible_movies)

        movie = Movies(
            title=possible_movies["original_title"],
            year=f"({possible_movies["release_date"].split("-")[0]})",
            description=possible_movies["overview"],
            img_url = f"https://image.tmdb.org/t/p/w500{possible_movies["poster_path"]}"
        )
        db.session.add(movie)
        db.session.commit()
        with app.app_context():

            update_movie = db.session.execute(db.select(Movies).where(Movies.title == possible_movies["original_title"])).scalar()
            movie.id = update_movie.id

        return redirect(url_for("edit",id = movie.id))

    return render_template("add.html", form= form)

if __name__ == '__main__':
    app.run(debug=True)

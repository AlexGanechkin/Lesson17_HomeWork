# app.py

from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False}
db = SQLAlchemy(app)

api = Api(app)
movie_ns = api.namespace('movies')
director_ns = api.namespace('directors')
genre_ns = api.namespace('genres')


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))


class MovieSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    director_id = fields.Int()


class DirectorSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


class GenreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


movies_schema = MovieSchema(many=True)
movie_schema = MovieSchema()

directors_schema = DirectorSchema(many=True)
director_schema = DirectorSchema()

genres_schema = GenreSchema(many=True)
genre_schema = GenreSchema()


@movie_ns.route('/')
class MoviesView(Resource):
    """ ?????? ???????????????? ???????????? ?????????????? ???? ????????, ?? ?????????? ?????????????????? ?????????? ?????????? ?? ???????? """

    def post(self):
        """ ?????????? ?????????????????? ?????????? ?????????? ?? ????????, ???????? ???????????????? ???? ?????????? """
        movie_json = request.json
        new_movie = Movie(**movie_json)
        movie_titles = Movie.query.filter(Movie.title == new_movie.title).count()
        if movie_titles > 0:
            return "?????????? ?? ?????????? ?????????????????? ?????? ???????????????????????? ?? ????????", 404
        db.session.add(new_movie)
        db.session.commit()
        return "?????????? ?????????? ???????????????? ?? ????????", 201

    def get(self):
        """
        ?????????? ???????????????? ???????????? ???????????? ??????????????, ?????????????????? ?? ????????, ???????? ????????????, ?????????????????????????????? ???? ?????????????????? ??/??????
        ?????????? ???????????? (?? ?????????????????????? ???? ?????????????????? ???????????????????? ?????????????????? ????????????). ???????????????????????? ???????????????? ???? ??????????????
        ?????????????????? ?? ?????????? ?? ????????.
        """
        director = request.args.get('director_id')
        genre = request.args.get('genre_id')

        if director is not None and genre is not None:
            movies = Movie.query.filter(Movie.director_id == director, Movie.genre_id == genre)
        elif director is not None:
            movies = Movie.query.filter(Movie.director_id == director)
        elif genre is not None:
            movies = Movie.query.filter(Movie.genre_id == genre)
        else:
            movies = Movie.query.all()

        movies_list = movies_schema.dump(movies)

        if not movies_list:
            if Director.query.get(director) is None:
                return "?????????????????? ?? ?????????????????????? id ?????? ?? ????????", 404
            elif Genre.query.get(genre) is None:
                return "?????????? ?? ?????????????????????? id ?????? ?? ????????", 404

            if director is not None and genre is not None:
                return f"???????????? ?????????????????? - {Director.query.get(director).name} - " \
                       f"?? ?????????? - {Genre.query.get(genre).name} - ?? ???????? ???? ??????????????", 404
            elif director is not None:
                return f"???????????? ?????????????????? - {Director.query.get(director).name} - ?? ???????? ???? ??????????????", 404
            elif genre is not None:
                return f"???????????? ?? ?????????? - {Genre.query.get(genre).name} - ?? ???????? ???? ??????????????", 404

        return movies_list, 200


@movie_ns.route('/<int:movie_id>')
class MovieView(Resource):
    """ ?????? ???????????????? ???????? ?????????? ???? ???????? ?????????????????????? ???? ???????? ???? ???????? """

    def get(self, movie_id):
        """
        ?????????? ???????????????? ?????????? ???? ???????????????????????? id, ?? ?????????? ?????????????????? ???????? ???? ???????????? ?? ???????? ?????????? ?? ?????????? id
        """
        movie = Movie.query.get(movie_id)
        if not movie:
            return "?????????? c ?????????????????????? id ???? ????????????", 404
        return movie_schema.dump(movie), 200

    def put(self, movie_id):
        """ ?????????? ?????????????????? ???????????? ???? ???????????? ?? ?????????????????????? id, ???????? ???????????????? ?????????????? ???????????? ?? ???????? """
        json_data = request.json
        movie = Movie.query.get(movie_id)
        if not movie:
            return "?????????? c ?????????????????????? id ???? ????????????", 404

        movie.title = json_data.get('title')
        movie.description = json_data.get('description')
        movie.trailer = json_data.get('trailer')
        movie.year = json_data.get('year')
        movie.rating = json_data.get('rating')
        movie.genre_id = json_data.get('genre_id')
        movie.director_id = json_data.get('director_id')

        db.session.add(movie)
        db.session.commit()
        return f"?????????? ?? id - {movie_id} - ?????? ????????????????", 204

    def delete(self, movie_id):
        """ ?????????? ?????????????? ?????????? ?? ?????????????????????? id, ???????? ???????????????? ?????????????? ???????????? ?? ???????? """
        movie = Movie.query.get(movie_id)
        if not movie:
            return "?????????? c ?????????????????????? id ???? ????????????", 404
        db.session.delete(movie)
        db.session.commit()
        return f"?????????? ?? id - {movie_id} - ?????? ???????????? ???? ????????", 204


@director_ns.route('/')
class DirectorView(Resource):
    """ ?????? ???????????????? ???????????? ???????????????????? ???? ????????, ?? ?????????? ?????????????????? ???????????? ?????????????????? ?? ???????? """

    def get(self):
        """ ?????????? ???????????????? ???????????? ???????????? ????????????????????, ?????????????????? ?? ???????? """
        directors = Director.query.all()
        return directors_schema.dump(directors)

    def post(self):
        """ ?????????? ?????????????????? ???????????? ?????????????????? ?? ????????, ???????? ???????????????? ???? ?????????? """
        director_json = request.json
        new_director = Director(**director_json)
        director_names = Director.query.filter(Director.name == new_director.name).count()
        if director_names > 0:
            return "???????????????? ?? ?????????? ???????????? ?????? ???????????????????????? ?? ????????", 404
        db.session.add(new_director)
        db.session.commit()
        return "?????????? ???????????????? ???????????????? ?? ????????", 201


@director_ns.route('/<int:director_id>')
class DirectorView(Resource):
    """ ?????? ???????????????????????? ???????????????????? ?????? ???????????????????????? ?? ???????? """

    def get(self, director_id):
        """
        ?????????? ???????????????? ?????????????????? ???? ???????????????????????? id, ?? ?????????? ?????????????????? ???????? ???? ???????????? ?? ???????? ???????????????? ?? ?????????? id
        """
        director = Director.query.get(director_id)
        if not director:
            return "???????????????? c ?????????????????????? id ???? ????????????", 404
        return director_schema.dump(director), 200

    def put(self, director_id):
        """ ?????????? ?????????????????? ???????????? ???? ?????????????????? ?? ?????????????????????? id, ???????? ???????????????? ?????????????? ?????????????????? ?? ???????? """
        json_data = request.json
        director = Director.query.get(director_id)
        if not director:
            return "???????????????? c ?????????????????????? id ???? ????????????", 404
        director.name = json_data.get('name')
        db.session.add(director)
        db.session.commit()
        return f"???????????????? ?? id - {director_id} - ?????? ????????????????", 204

    def delete(self, director_id):
        """ ?????????? ?????????????? ?????????????????? ?? ?????????????????????? id, ???????? ???????????????? ?????????????? ?????????????????? ?? ???????? """
        director = Director.query.get(director_id)
        if not director:
            return "???????????????? c ?????????????????????? id ???? ????????????", 404
        db.session.delete(director)
        db.session.commit()
        return f"???????????????? ?? id - {director_id} - ?????? ???????????? ???? ????????", 204


@genre_ns.route('/')
class GenreView(Resource):
    """ ?????? ???????????????? ???????????? ???????????? ???? ????????, ?? ?????????? ?????????????????? ?????????? ???????? ?? ???????? """

    def get(self):
        """ ?????????? ???????????????? ???????????? ???????????? ????????????, ?????????????????? ?? ???????? """
        genres = Genre.query.all()
        return genres_schema.dump(genres)

    def post(self):
        """ ?????????? ?????????????????? ?????????? ???????? ?? ????????, ???????? ???????????????? ???? ?????????? """
        genre_json = request.json
        new_genre = Genre(**genre_json)
        genre_names = Genre.query.filter(Genre.name == new_genre.name).count()
        if genre_names > 0:
            return "???????? ?? ?????????? ?????????????????? ?????? ???????????????????????? ?? ????????", 404
        db.session.add(new_genre)
        db.session.commit()
        return "?????????? ???????? ???????????????? ?? ????????", 201


@genre_ns.route('/<int:genre_id>')
class GenreView(Resource):
    """ ?????? ???????????????????????? ???????? ?????? ???????????????????????? ?? ???????? """

    def get(self, genre_id):
        """
        ?????????? ???????????????? ???????? ???? ???????????????????????? id, ?? ?????????? ?????????????????? ???????? ???? ???????????? ?? ???????? ???????? ?? ?????????? id
        """
        genre = Genre.query.get(genre_id)
        genre_movies = db.session.query(Movie.title).filter(Movie.genre_id == genre_id).all()
        if not genre:
            return "???????? c ?????????????????????? id ???? ????????????", 404
        return (genre_schema.dump(genre), movies_schema.dump(genre_movies)), 200

    def put(self, genre_id):
        """ ?????????? ?????????????????? ???????????? ???? ?????????? ?? ?????????????????????? id, ???????? ???????????????? ?????????????? ?????????????????? ?? ???????? """
        json_data = request.json
        genre = Genre.query.get(genre_id)
        if not genre:
            return "???????? c ?????????????????????? id ???? ????????????", 404
        genre.name = json_data.get('name')
        db.session.add(genre)
        db.session.commit()
        return f"???????? ?? id - {genre_id} - ?????? ????????????????", 204

    def delete(self, genre_id):
        """ ?????????? ?????????????? ???????? ?? ?????????????????????? id, ???????? ???????????????? ?????????????? ?????????????????? ?? ???????? """
        genre = Genre.query.get(genre_id)
        if not genre:
            return "???????? c ?????????????????????? id ???? ????????????", 404
        db.session.delete(genre)
        db.session.commit()
        return f"???????????????? ?? id - {genre_id} - ?????? ???????????? ???? ????????", 204


if __name__ == '__main__':
    app.run(debug=True)

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
    id = db.Column(db.Integer, primary_key=True)
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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
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


movies_schema = MovieSchema(many=True)
movie_schema = MovieSchema()


@movie_ns.route('/')
class MoviesView(Resource):
    """ Рут получает список фильмов со всей информацией по каждому фильму из базы """

    def get(self):
        """
        Метод получает полный список фильмов, имеющийся в базе, либо список, отфильтрованный по режиссеру и/или
        жанру фильма (в зависимости от введенных параметров поисковой строки). Присутствует проверка на наличие
        режиссера и жанра в базе.
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
            if director is not None and genre is not None:
                return f"Фильмы режиссера - {Director.query.get(director).name} - " \
                       f"в жанре - {Genre.query.get(genre).name} - в базе не найдены", 404
            elif director is not None:
                if Director.query.get(director) is not None:
                    return f"Фильмы режиссера - {Director.query.get(director).name} - в базе не найдены", 404
                else:
                    return "Режиссера с запрошенным id нет в базе", 404
            elif genre is not None:
                if Genre.query.get(genre) is not None:
                    return f"Фильмы в жанре - {Genre.query.get(genre).name} - в базе не найдены", 404
                else:
                    return "Жанра с запрошенным id нет в базе", 404

        return movies_list, 200


@movie_ns.route('/<int:id>')
class MovieView(Resource):
    """ Рут получает один фильм со всей информацией по нему из базы """

    def get(self, movie_id):
        """
        Метод получает фильм по запрошенному id, а также проверяет есть ли вообще в базе фильм с таким id
        """
        movie = Movie.query.get(movie_id)
        if not movie:
            return "Фильм c запрошенным id не найден", 404
        return movie_schema.dump(movie), 200


@director_ns.route('/')
class DirectorView(Resource):
    """ Рут добавляет нового режиссера в базу """

    def post(self):
        """ Метод добавляет нового режиссера в базу, есть проверка на дубли """
        director_json = request.json
        new_director = Director(**director_json)
        if Director.query.get(director_json['id']):
            return "Режиссер с таким id уже присутствует в базе", 404
        db.session.add(new_director)
        db.session.commit()
        return "Новый режиссер добавлен в базу", 201


@director_ns.route('/<int:director_id>')
class DirectorView(Resource):
    """ Рут обрабатывает режиссера уже существующего в базе """

    def put(self, director_id):
        """ Метод обновляет данные по режиссеру с запрошенным id, есть проверка наличия режиссера в базе """
        json_data = request.json
        director = Director.query.get(director_id)
        if not director:
            return "Режиссер c запрошенным id не найден", 404
        director.name = json_data.get('name')
        db.session.add(director)
        db.session.commit()
        return f"Режиссер с id - {director_id} - был обновлен", 204

    def delete(self, director_id):
        """ Метод удаляет режиссера с запрошенным id, есть проверка наличия режиссера в базе """
        director = Director.query.get(director_id)
        if not director:
            return "Режиссер c запрошенным id не найден", 404
        db.session.delete(director)
        db.session.commit()
        return f"Режиссер с id - {director_id} - был удален из базы", 204


@genre_ns.route('/')
class GenreView(Resource):
    """ Рут добавляет новый жанр в базу """

    def post(self):
        """ Метод добавляет новый жанр в базу, есть проверка на дубли """
        genre_json = request.json
        new_genre = Genre(**genre_json)
        if Genre.query.get(genre_json['id']):
            return "Жанр с таким id уже присутствует в базе", 404
        db.session.add(new_genre)
        db.session.commit()
        return "Новый жанр добавлен в базу", 201


@genre_ns.route('/<int:genre_id>')
class GenreView(Resource):
    """ Рут обрабатывает жанр уже существующий в базе """

    def put(self, genre_id):
        """ Метод обновляет данные по жанру с запрошенным id, есть проверка наличия режиссера в базе """
        json_data = request.json
        genre = Genre.query.get(genre_id)
        if not genre:
            return "Жанр c запрошенным id не найден", 404
        genre.name = json_data.get('name')
        db.session.add(genre)
        db.session.commit()
        return f"Жанр с id - {genre_id} - был обновлен", 204

    def delete(self, genre_id):
        """ Метод удаляет жанр с запрошенным id, есть проверка наличия режиссера в базе """
        genre = Genre.query.get(genre_id)
        if not genre:
            return "Жанр c запрошенным id не найден", 404
        db.session.delete(genre)
        db.session.commit()
        return f"Режиссер с id - {genre_id} - был удален из базы", 204


if __name__ == '__main__':
    app.run(debug=True)

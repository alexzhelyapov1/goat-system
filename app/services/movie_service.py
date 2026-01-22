from app import db
from app.models import Movie
from app.schemas import MovieCreate

class MovieService:
    @staticmethod
    def get_movies_by_user(user_id):
        return Movie.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_movie(movie_id):
        return Movie.query.get(movie_id)

    @staticmethod
    def create_movie(movie_data: MovieCreate, user_id: int):
        movie = Movie(**movie_data.model_dump(), user_id=user_id)
        db.session.add(movie)
        db.session.commit()
        return movie

    @staticmethod
    def update_movie(movie_id, movie_data: MovieCreate):
        movie = Movie.query.get(movie_id)
        for key, value in movie_data.model_dump(exclude_unset=True).items():
            setattr(movie, key, value)
        db.session.commit()
        return movie

    @staticmethod
    def delete_movie(movie_id):
        movie = Movie.query.get(movie_id)
        db.session.delete(movie)
        db.session.commit()

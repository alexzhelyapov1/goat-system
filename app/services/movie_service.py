from sqlalchemy.orm import Session
from app.models import Movie
from app.schemas import MovieCreate

class MovieService:
    @staticmethod
    def get_movies_by_user(db: Session, user_id: int):
        return db.query(Movie).filter_by(user_id=user_id).all()

    @staticmethod
    def get_movie(db: Session, movie_id: int):
        return db.query(Movie).get(movie_id)

    @staticmethod
    def create_movie(db: Session, movie_data: MovieCreate, user_id: int):
        movie = Movie(**movie_data.model_dump(), user_id=user_id)
        db.add(movie)
        db.commit()
        db.refresh(movie)
        return movie

    @staticmethod
    def update_movie(db: Session, movie_id: int, movie_data: MovieCreate):
        movie = db.query(Movie).get(movie_id)
        if not movie:
            return None
        for key, value in movie_data.model_dump(exclude_unset=True).items():
            setattr(movie, key, value)
        db.commit()
        db.refresh(movie)
        return movie

    @staticmethod
    def delete_movie(db: Session, movie_id: int):
        movie = db.query(Movie).get(movie_id)
        if movie:
            db.delete(movie)
            db.commit()

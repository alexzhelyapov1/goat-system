from app.models import Movie
from app.schemas import MovieCreate
from sqlalchemy.orm import Session

class MovieService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_movies_by_user(self, user_id):
        return self.db_session.query(Movie).filter_by(user_id=user_id).all()

    def get_movie(self, movie_id):
        return self.db_session.query(Movie).get(movie_id)

    def create_movie(self, movie_data: MovieCreate, user_id: int):
        movie = Movie(**movie_data.model_dump(), user_id=user_id)
        self.db_session.add(movie)
        self.db_session.commit()
        self.db_session.refresh(movie)
        return movie

    def update_movie(self, movie_id, movie_data: MovieCreate):
        movie = self.db_session.query(Movie).get(movie_id)
        if not movie:
            return None
        for key, value in movie_data.model_dump(exclude_unset=True).items():
            setattr(movie, key, value)
        self.db_session.commit()
        self.db_session.refresh(movie)
        return movie

    def delete_movie(self, movie_id):
        movie = self.db_session.query(Movie).get(movie_id)
        if movie:
            self.db_session.delete(movie)
            self.db_session.commit()
        return movie

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.services.movie_service import MovieService
from app.schemas import MovieSchema, MovieCreate
from app.auth.dependencies import get_current_user, get_db
from app.models import User
from typing import List
from app.services.movie_service import MovieService

router = APIRouter(
    prefix="/movies",
    tags=["movies"],
)

@router.get("/", response_model=List[MovieSchema])
def get_movies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    movies = MovieService.get_movies_by_user(db, current_user.id)
    return [MovieSchema.model_validate(m) for m in movies]

@router.post("/", response_model=MovieSchema)
def create_movie(movie: MovieCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_movie = MovieService.create_movie(db, movie, current_user.id)
    return MovieSchema.model_validate(new_movie)

@router.get("/{movie_id}", response_model=MovieSchema)
def get_movie(movie_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    movie = MovieService.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this movie")
    return MovieSchema.model_validate(movie)

@router.put("/{movie_id}", response_model=MovieSchema)
def update_movie(movie_id: int, movie: MovieCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_movie = MovieService.get_movie(db, movie_id)
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if existing_movie.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this movie")
    updated_movie = MovieService.update_movie(db, movie_id, movie)
    return MovieSchema.model_validate(updated_movie)

@router.delete("/{movie_id}", status_code=204)
def delete_movie(movie_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_movie = MovieService.get_movie(db, movie_id)
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if existing_movie.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this movie")
    MovieService.delete_movie(db, movie_id)
    return

@router.get("/export", response_model=List[dict])
def export_movies(fields: List[str] = Query(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    movies = MovieService.get_movies_by_user(db, current_user.id)
    movies_to_export = []
    for movie in movies:
        movie_dict = MovieSchema.model_validate(movie).model_dump(mode="json")
        exported_movie = {field: movie_dict.get(field) for field in fields}
        movies_to_export.append(exported_movie)
    return movies_to_export

@router.post("/import")
def import_movies(movies_data: List[MovieCreate], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for movie_data in movies_data:
        MovieService.create_movie(db, movie_data, current_user.id)
    return {"message": "Movies imported successfully!"}

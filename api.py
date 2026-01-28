from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models import User, Task, Habit, Movie # Added Movie
from app.services.task_service import TaskService
from app.services.habit_service import HabitService
from app.services.movie_service import MovieService # Added MovieService
from app.schemas import TaskSchema, UserSchema, TaskCreate, HabitSchema, HabitCreate, HabitLogCreate, HabitLogSchema, MovieSchema, MovieCreate # Added Movie schemas
from app.auth.security import get_current_user

app = FastAPI()

# Task Router
task_router = APIRouter(
    tags=["tasks"],
    dependencies=[Depends(get_current_user), Depends(get_db)],
)


@task_router.get("/tasks", response_model=List[TaskSchema])
async def get_all_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    task_type: Optional[str] = None
):
    task_service = TaskService(db_session=db)
    tasks = task_service.get_tasks_by_user_and_type(current_user.id, task_type)
    return tasks


@task_router.get("/tasks/{task_id}", response_model=TaskSchema)
async def get_task_by_id(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task_service = TaskService(db_session=db)
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    return task


@task_router.post("/tasks", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task_service = TaskService(db_session=db)
    new_task = task_service.create_task(task_data, current_user.id)
    return new_task


@task_router.put("/tasks/{task_id}", response_model=TaskSchema)
async def update_existing_task(
    task_id: int,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task_service = TaskService(db_session=db)
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
    updated_task = task_service.update_task(task_id, task_data)
    return updated_task


@task_router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task_service = TaskService(db_session=db)
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    task_service.delete_task(task_id)
    return {"message": "Task deleted successfully"}

# Habit Router
habit_router = APIRouter(
    tags=["habits"],
    dependencies=[Depends(get_current_user), Depends(get_db)],
)

@habit_router.get("/habits", response_model=List[HabitSchema])
async def get_all_habits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit_service = HabitService(db_session=db)
    habits = habit_service.get_habits_by_user(current_user.id)
    return habits

@habit_router.get("/habits/{habit_id}", response_model=HabitSchema)
async def get_habit_by_id(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit_service = HabitService(db_session=db)
    habit = habit_service.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this habit")
    return habit

@habit_router.post("/habits", response_model=HabitSchema, status_code=status.HTTP_201_CREATED)
async def create_new_habit(
    habit_data: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit_service = HabitService(db_session=db)
    new_habit = habit_service.create_habit(habit_data, current_user.id)
    return new_habit

@habit_router.put("/habits/{habit_id}", response_model=HabitSchema)
async def update_existing_habit(
    habit_id: int,
    habit_data: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit_service = HabitService(db_session=db)
    habit = habit_service.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this habit")
    updated_habit = habit_service.update_habit(habit_id, habit_data)
    return updated_habit

@habit_router.delete("/habits/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_habit(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit_service = HabitService(db_session=db)
    habit = habit_service.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this habit")
    habit_service.delete_habit(habit_id)
    return {"message": "Habit deleted successfully"}

@habit_router.put("/habits/{habit_id}/log", response_model=HabitLogSchema) # Using PUT for idempotency
async def log_habit_entry(
    habit_id: int,
    log_data: HabitLogCreate, # Use HabitLogCreate for request body
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit_service = HabitService(db_session=db)
    habit = habit_service.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to log for this habit")

    # Ensure habit_id in path matches habit_id in log_data
    if log_data.habit_id != habit_id:
        raise HTTPException(status_code=400, detail="Habit ID in path does not match habit ID in body")

    logged_habit = habit_service.log_habit(
        habit_id=habit_id,
        log_date=log_data.date,
        is_done=log_data.is_done,
        index=log_data.index
    )
    return logged_habit

@habit_router.get("/habits/{habit_id}/logs", response_model=List[HabitLogSchema])
async def get_habit_logs_for_habit(
    habit_id: int,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit_service = HabitService(db_session=db)
    habit = habit_service.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access logs for this habit")

    logs = habit_service.get_habit_logs(habit_id, start_date, end_date)
    return logs

# Movie Router
movie_router = APIRouter(
    tags=["movies"],
    dependencies=[Depends(get_current_user), Depends(get_db)],
)

@movie_router.get("/movies", response_model=List[MovieSchema])
async def get_all_movies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie_service = MovieService(db_session=db)
    movies = movie_service.get_movies_by_user(current_user.id)
    return movies

@movie_router.get("/movies/{movie_id}", response_model=MovieSchema)
async def get_movie_by_id(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie_service = MovieService(db_session=db)
    movie = movie_service.get_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this movie")
    return movie

@movie_router.post("/movies", response_model=MovieSchema, status_code=status.HTTP_201_CREATED)
async def create_new_movie(
    movie_data: MovieCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie_service = MovieService(db_session=db)
    new_movie = movie_service.create_movie(movie_data, current_user.id)
    return new_movie

@movie_router.put("/movies/{movie_id}", response_model=MovieSchema)
async def update_existing_movie(
    movie_id: int,
    movie_data: MovieCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie_service = MovieService(db_session=db)
    movie = movie_service.get_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this movie")
    updated_movie = movie_service.update_movie(movie_id, movie_data)
    return updated_movie

@movie_router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_movie(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie_service = MovieService(db_session=db)
    movie = movie_service.get_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this movie")
    movie_service.delete_movie(movie_id)
    return {"message": "Movie deleted successfully"}

# Include the router in the main FastAPI app
app.include_router(task_router)
app.include_router(habit_router, prefix="/api") # Add the habit router with a prefix
app.include_router(movie_router, prefix="/api") # Add the movie router with a prefix


@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}


@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    return {"user_count": user_count}


@app.get("/test-service", response_model=List[TaskSchema])
async def test_service(db: Session = Depends(get_db)):
    task_service = TaskService(db_session=db)
    # Assuming user with ID 1 exists for this test
    tasks = task_service.get_all_tasks_for_user(user_id=1)
    return tasks


@app.get("/test-secure", response_model=UserSchema)
async def test_secure_endpoint(current_user: User = Depends(get_current_user)):
    return current_user

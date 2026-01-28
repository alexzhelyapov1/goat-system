from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.services.habit_service import HabitService
from app.schemas import HabitSchema, HabitCreate
from app.auth.dependencies import get_current_user, get_db
from app.models import User
from typing import List
from datetime import date

router = APIRouter(
    prefix="/habits",
    tags=["habits"],
)

class HabitLogBase(BaseModel):
    habit_id: int
    date: date
    is_done: bool
    index: int = 0

@router.get("/", response_model=List[HabitSchema])
def get_habits(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habits = HabitService.get_habits_by_user(db, current_user.id)
    return [HabitSchema.model_validate(h) for h in habits]

@router.post("/", response_model=HabitSchema)
def create_habit(habit: HabitCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_habit = HabitService.create_habit(db, habit, current_user.id)
    return HabitSchema.model_validate(new_habit)

@router.get("/{habit_id}", response_model=HabitSchema)
def get_habit(habit_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = HabitService.get_habit(db, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this habit")
    return HabitSchema.model_validate(habit)

@router.put("/{habit_id}", response_model=HabitSchema)
def update_habit(habit_id: int, habit: HabitCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_habit = HabitService.get_habit(db, habit_id)
    if not existing_habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if existing_habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this habit")
    updated_habit = HabitService.update_habit(db, habit_id, habit)
    return HabitSchema.model_validate(updated_habit)

@router.delete("/{habit_id}", status_code=204)
def delete_habit(habit_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_habit = HabitService.get_habit(db, habit_id)
    if not existing_habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if existing_habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this habit")
    HabitService.delete_habit(db, habit_id)
    return

@router.post("/log")
def log_habit(log_data: HabitLogBase, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    habit = HabitService.get_habit(db, log_data.habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to log this habit")
    HabitService.log_habit(db, log_data.habit_id, log_data.date, log_data.is_done, log_data.index)
    return {"success": True}

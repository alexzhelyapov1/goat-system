from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.task_service import TaskService
from app.schemas import TaskSchema, TaskCreate
from app.auth.dependencies import get_current_user, get_db
from app.models import User
from typing import List, Optional

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

@router.get("/", response_model=List[TaskSchema])
def get_tasks(type: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if type and type != 'all':
        tasks = TaskService.get_tasks_by_user_and_type(db, current_user.id, type)
    else:
        tasks = TaskService.get_all_tasks_for_user(db, current_user.id)
    return [TaskSchema.model_validate(t) for t in tasks]

@router.post("/", response_model=TaskSchema)
def create_task(task: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_task = TaskService.create_task(db, task, current_user.id)
    return TaskSchema.model_validate(new_task)

@router.get("/calendar", response_model=List[TaskSchema])
def get_calendar_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = TaskService.get_calendar_tasks(db, current_user.id)
    return [TaskSchema.model_validate(t) for t in tasks]

@router.get("/{task_id}", response_model=TaskSchema)
def get_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this task")
    return TaskSchema.model_validate(task)

@router.put("/{task_id}", response_model=TaskSchema)
def update_task(task_id: int, task: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_task = TaskService.get_task(db, task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    if existing_task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this task")
    updated_task = TaskService.update_task(db, task_id, task)
    return TaskSchema.model_validate(updated_task)

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_task = TaskService.get_task(db, task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    if existing_task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this task")
    TaskService.delete_task(db, task_id)
    return
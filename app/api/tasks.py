from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.services.task_service import TaskService
from app.schemas import TaskSchema, TaskCreate
from app.auth.dependencies import get_current_user, get_db
from app.models import User
from typing import List, Optional, Dict, Any

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

def _prepare_task_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processes raw task data dictionary to conform to the TaskCreate schema."""
    processed_data = data.copy()
    
    for key in ['deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at']:
        date_val = processed_data.get(f'{key}_date')
        time_val = processed_data.get(f'{key}_time')

        if date_val and str(date_val).strip():
            if not time_val or not str(time_val).strip():
                time_val = '00:00'
            processed_data[key] = f'{date_val}T{time_val}:00'
        else:
            processed_data[key] = None

    if 'duration' in processed_data and processed_data['duration'] is not None:
        try:
            processed_data['duration'] = int(processed_data['duration'])
        except (ValueError, TypeError):
            processed_data['duration'] = None # Or raise an error
    else:
        processed_data['duration'] = None

    if processed_data.get('planned_start'):
        processed_data['type'] = 'CALENDAR'
        
    # Remove helper fields
    helper_fields = [f'{k}_{p}' for k in ['deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at'] for p in ['date', 'time']]
    for field in helper_fields:
        processed_data.pop(field, None)
        
    return processed_data


@router.get("/", response_model=List[TaskSchema])
def get_tasks(type: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if type and type != 'all':
        tasks = TaskService.get_tasks_by_user_and_type(db, current_user.id, type)
    else:
        tasks = TaskService.get_all_tasks_for_user(db, current_user.id)
    return [TaskSchema.model_validate(t) for t in tasks]

@router.post("/", response_model=TaskSchema)
def create_task(
    task_data: Dict[str, Any] = Body(...), 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    prepared_data = _prepare_task_data(task_data)
    try:
        task_create_obj = TaskCreate(**prepared_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
        
    new_task = TaskService.create_task(db, task_create_obj, current_user.id)
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
def update_task(
    task_id: int, 
    task_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    existing_task = TaskService.get_task(db, task_id)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    if existing_task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this task")
    
    prepared_data = _prepare_task_data(task_data)
    try:
        task_update_obj = TaskCreate(**prepared_data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
        
    updated_task = TaskService.update_task(db, task_id, task_update_obj)
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


@router.get("/export", response_model=List[dict])
def export_tasks(fields: List[str] = Query(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = TaskService.get_all_tasks_for_user(db, current_user.id)
    tasks_to_export = []
    for task in tasks:
        task_dict = TaskSchema.model_validate(task).model_dump(mode="json")
        exported_task = {field: task_dict.get(field) for field in fields}
        tasks_to_export.append(exported_task)
    return tasks_to_export


@router.post("/import")
def import_tasks(tasks_data: List[TaskCreate], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for task_data in tasks_data:
        TaskService.create_task(db, task_data, current_user.id)
    return {"message": "Tasks imported successfully!"}
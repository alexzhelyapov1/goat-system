from sqlalchemy.orm import Session
from app.models import Task
from app.schemas import TaskCreate
from typing import List

class TaskService:
    @staticmethod
    def get_tasks_by_user_and_type(db: Session, user_id: int, task_type=None) -> List[Task]:
        query = db.query(Task).filter_by(user_id=user_id)
        if task_type:
            if task_type == 'all':
                query = query.filter(Task.type.in_(['CURRENT', 'ROUTINE', 'INBOX']))
            else:
                query = query.filter_by(type=task_type)
        return query.all()

    @staticmethod
    def get_calendar_tasks(db: Session, user_id: int) -> List[Task]:
        return db.query(Task).filter(Task.user_id == user_id, Task.planned_start != None).all()

    @staticmethod
    def get_all_tasks_for_user(db: Session, user_id: int) -> List[Task]:
        return db.query(Task).filter_by(user_id=user_id).all()

    @staticmethod
    def get_task(db: Session, task_id: int) -> Task:
        return db.query(Task).get(task_id)

    @staticmethod
    def create_task(db: Session, task_data: TaskCreate, user_id: int) -> Task:
        task = Task(**task_data.model_dump(exclude_unset=True), user_id=user_id)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: TaskCreate) -> Task:
        task = db.query(Task).get(task_id)
        if not task:
            return None
        for key, value in task_data.model_dump(exclude_unset=True).items():
            setattr(task, key, value)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int):
        task = db.query(Task).get(task_id)
        if task:
            db.delete(task)
            db.commit()

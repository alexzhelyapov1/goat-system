from app import db
from app.models import Task
from app.schemas import TaskCreate
from flask_login import current_user

class TaskService:
    @staticmethod
    def get_tasks_by_user_and_type(user_id, task_type=None):
        query = Task.query.filter_by(user_id=user_id)
        if task_type:
            if task_type == 'all':
                query = query.filter(Task.type.in_(['CURRENT', 'ROUTINE', 'INBOX']))
            else:
                query = query.filter_by(type=task_type)
        return query.all()

    @staticmethod
    def get_task(task_id):
        return Task.query.get(task_id)

    @staticmethod
    def create_task(task_data: TaskCreate):
        task = Task(**task_data.model_dump(exclude_unset=True), user_id=current_user.id)
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def update_task(task_id, task_data: TaskCreate):
        task = Task.query.get(task_id)
        for key, value in task_data.model_dump(exclude_unset=True).items():
            setattr(task, key, value)
        db.session.commit()
        return task

    @staticmethod
    def delete_task(task_id):
        task = Task.query.get(task_id)
        db.session.delete(task)
        db.session.commit()

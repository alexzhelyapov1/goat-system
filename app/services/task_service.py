from sqlalchemy.orm import Session
from app.models import Task
from app.schemas import TaskCreate

class TaskService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_tasks_by_user_and_type(self, user_id, task_type=None):
        query = self.db.query(Task).filter_by(user_id=user_id)
        if task_type:
            if task_type == 'all':
                query = query.filter(Task.type.in_(['CURRENT', 'ROUTINE', 'INBOX']))
            else:
                query = query.filter_by(type=task_type)
        return query.all()

    def get_all_tasks_for_user(self, user_id):
        return self.db.query(Task).filter_by(user_id=user_id).all()

    def get_task(self, task_id):
        return self.db.query(Task).get(task_id)

    def create_task(self, task_data: TaskCreate, user_id: int):
        task = Task(**task_data.model_dump(exclude_unset=True), user_id=user_id)
        self.db.add(task)
        self.db.commit()
        return task

    def update_task(self, task_id, task_data: TaskCreate):
        task = self.db.query(Task).get(task_id)
        for key, value in task_data.model_dump(exclude_unset=True).items():
            setattr(task, key, value)
        self.db.commit()
        return task

    def delete_task(self, task_id):
        task = self.db.query(Task).get(task_id)
        self.db.delete(task)
        self.db.commit()

    @staticmethod
    def _prepare_data_from_form(form_data: dict) -> dict:
        """Helper to process raw form data for task creation/updates."""
        processed_data = form_data.copy()

        for key in ['deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at']:
            date_val = processed_data.get(f'{key}_date')
            time_val = processed_data.get(f'{key}_time')

            if date_val:
                if not time_val:
                    time_val = '00:00'
                # Combine date and time, assuming a default timezone if not provided.
                # The format should be ISO 8601 compatible.
                processed_data[key] = f'{date_val}T{time_val}:00' # Basic ISO format
            else:
                processed_data[key] = None
        
        if not processed_data.get('duration'):
            processed_data['duration'] = None

        if processed_data.get('planned_start'):
            processed_data['type'] = 'CALENDAR'
            
        return processed_data

from apscheduler.schedulers.background import BackgroundScheduler
from app.models import Task, TaskType
from app import db
from datetime import datetime

def check_suspended_tasks(app):
    with app.app_context():
        tasks = Task.query.filter(Task.suspend_due <= datetime.utcnow()).all()
        for task in tasks:
            task.type = TaskType.CURRENT
            task.suspend_due = None
        db.session.commit()

def check_notifications(app):
    with app.app_context():
        tasks = Task.query.filter(Task.notify_at <= datetime.utcnow()).all()
        for task in tasks:
            print(f"Notification for task: {task.title}")
            task.notify_at = None
        db.session.commit()

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_suspended_tasks, args=[app], trigger="interval", seconds=60)
    scheduler.add_job(func=check_notifications, args=[app], trigger="interval", seconds=60)
    scheduler.start()

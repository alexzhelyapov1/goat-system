from apscheduler.schedulers.background import BackgroundScheduler
from app.models import Task, TaskType
from app import db
from datetime import datetime, timedelta, timezone
from app.queue import q

def check_tasks(app):
    with app.app_context():
        now = datetime.now(timezone.utc)
        
        # Check suspended tasks
        suspended_tasks = Task.query.filter(Task.suspend_due <= now).all()
        for task in suspended_tasks:
            task.type = TaskType.CURRENT
            task.suspend_due = None

        # Check notifications
        
        # Notify_at
        tasks_to_notify = Task.query.filter(Task.notify_at <= now, Task.notify_at != None).all()
        for task in tasks_to_notify:
            if task.author.telegram_chat_id:
                message = f"Reminder for task: {task.title} (ID: {task.id})"
                q.enqueue('app.tasks_rq.send_telegram_message', task.author.telegram_chat_id, message)
            task.notify_at = None

        # Planned_start
        one_hour_from_now = now + timedelta(hours=1)
        tasks_to_remind = Task.query.filter(
            Task.planned_start > now, 
            Task.planned_start <= one_hour_from_now,
            Task.planned_start_notified == False
        ).all()
        for task in tasks_to_remind:
            if task.author.telegram_chat_id:
                message = f"Task starting soon: {task.title} (ID: {task.id})"
                q.enqueue('app.tasks_rq.send_telegram_message', task.author.telegram_chat_id, message)
                task.planned_start_notified = True

        db.session.commit()

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_tasks, args=[app], trigger="interval", seconds=3)
    scheduler.start()

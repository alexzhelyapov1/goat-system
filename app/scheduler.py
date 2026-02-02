from apscheduler.schedulers.background import BackgroundScheduler
from app.models import Task, TaskType
from app.database import SessionLocal
from datetime import datetime, timedelta, timezone
from app.queue import q

def check_tasks():
    db_session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # Check suspended tasks
        suspended_tasks = db_session.query(Task).filter(Task.suspend_due <= now).all()
        for task in suspended_tasks:
            task.type = TaskType.CURRENT
            task.suspend_due = None

        # Check notifications
        
        # Notify_at
        tasks_to_notify = db_session.query(Task).filter(Task.notify_at <= now, Task.notify_at != None).all()
        for task in tasks_to_notify:
            if task.author.telegram_chat_id:
                message = f"Reminder for task: {task.title} (ID: {task.id})"
                q.enqueue('app.tasks_rq.send_telegram_message', task.author.telegram_chat_id, message)
            task.notify_at = None

        # Planned_start
        one_hour_from_now = now + timedelta(hours=1)
        tasks_to_remind = db_session.query(Task).filter(
            Task.planned_start > now, 
            Task.planned_start <= one_hour_from_now,
            Task.planned_start_notified == False
        ).all()
        for task in tasks_to_remind:
            if task.author.telegram_chat_id:
                message = f"Task starting soon: {task.title} (ID: {task.id})"
                q.enqueue('app.tasks_rq.send_telegram_message', task.author.telegram_chat_id, message)
                task.planned_start_notified = True

        db_session.commit()
    finally:
        db_session.close()

def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_tasks, trigger="interval", seconds=60)
    scheduler.start()

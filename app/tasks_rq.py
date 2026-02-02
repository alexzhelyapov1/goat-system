from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.schemas import TaskCreate
from app.database import SessionLocal
from app.telegram_utils import send_telegram_message, run_async_in_new_loop

def handle_task_list(chat_id, task_type):
    """Fetches and sends a list of tasks to the user."""
    db_session = SessionLocal()
    try:
        user = UserService.get_user_by_telegram_chat_id(db_session, str(chat_id))
        if not user:
            run_async_in_new_loop(send_telegram_message(chat_id, "Your account is not linked."))
            return

        tasks = TaskService.get_tasks_by_user_and_type(db_session, user.id, task_type)
        if tasks:
            message = f"Tasks for type: {task_type}\n\n"
            for task in tasks:
                message += f"- {task.title} (ID: {task.id})\n"
        else:
            message = "No tasks found for this type."
        run_async_in_new_loop(send_telegram_message(chat_id, message))
    finally:
        db_session.close()

def create_task(user_id, task_data_dict):
    """Creates a new task."""
    db_session = SessionLocal()
    try:
        task_data = TaskCreate(**task_data_dict)
        TaskService.create_task(db_session, task_data, user_id)
        user = UserService.get_user_by_id(db_session, user_id)
        if user and user.telegram_chat_id:
            run_async_in_new_loop(send_telegram_message(
                user.telegram_chat_id,
                f"Task '{task_data.title}' created successfully."
            ))
    finally:
        db_session.close()

def delete_task(user_id, task_id):
    """Deletes a task."""
    db_session = SessionLocal()
    try:
        task = TaskService.get_task(db_session, task_id)
        user = UserService.get_user_by_id(db_session, user_id)
        if not user or not user.telegram_chat_id:
            return

        if task and task.user_id == user_id:
            task_title = task.title
            TaskService.delete_task(db_session, task_id)
            run_async_in_new_loop(send_telegram_message(
                user.telegram_chat_id,
                f"Task '{task_title}' deleted successfully."
            ))
        else:
            run_async_in_new_loop(send_telegram_message(
                user.telegram_chat_id,
                "Task not found or you are not authorized to delete it."
            ))
    finally:
        db_session.close()

import telegram
import asyncio
from app import create_app
from app.models import User, Task
from app.services.task_service import TaskService
from app.schemas import TaskCreate

def send_telegram_message(chat_id, text):
    """Sends a message to a telegram chat."""
    app = create_app()
    if app.config['TELEGRAM_BOT_TOKEN']:
        try:
            bot = telegram.Bot(token=app.config['TELEGRAM_BOT_TOKEN'])
            # Using asyncio.run() is acceptable here as RQ workers are synchronous.
            asyncio.run(bot.send_message(chat_id=chat_id, text=text))
        except Exception as e:
            with app.app_context():
                app.logger.error(f"Failed to send message to {chat_id}: {e}")

def handle_task_list(chat_id, task_type):
    """Fetches and sends a list of tasks to the user."""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()
        if not user:
            send_telegram_message(chat_id, "Your account is not linked. Please use /start to link your account.")
            return

        tasks = TaskService.get_tasks_by_user_and_type(user.id, task_type)
        if tasks:
            message = f"Tasks for type: {task_type}\n\n"
            for task in tasks:
                message += f"- {task.title} (ID: {task.id})\n"
        else:
            message = "No tasks found for this type."
        send_telegram_message(chat_id, message)

def create_task(user_id, task_data_dict):
    """Creates a new task."""
    app = create_app()
    with app.app_context():
        task_data = TaskCreate(**task_data_dict)
        TaskService.create_task(task_data, user_id)
        user = User.query.get(user_id)
        if user and user.telegram_chat_id:
            send_telegram_message(
                user.telegram_chat_id,
                f"Task '{task_data.title}' created successfully."
            )

def delete_task(user_id, task_id):
    """Deletes a task."""
    app = create_app()
    with app.app_context():
        task = TaskService.get_task(task_id)
        user = User.query.get(user_id)
        if not user or not user.telegram_chat_id:
            return 

        if task and task.user_id == user_id:
            task_title = task.title
            TaskService.delete_task(task_id)
            send_telegram_message(
                user.telegram_chat_id,
                f"Task '{task_title}' deleted successfully."
            )
        else:
            send_telegram_message(
                user.telegram_chat_id,
                f"Task not found or you are not authorized to delete it."
            )

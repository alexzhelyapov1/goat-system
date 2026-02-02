import logging
from datetime import datetime
from functools import wraps

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from app.models import UserRole
from app.schemas import TaskCreate
from app.queue import q, redis_conn
from app.database import SessionLocal
from app.services.user_service import UserService
from app.services.task_service import TaskService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CONFIRM_DELETE = 0
GET_TITLE, GET_NOTIFY_CHOICE, GET_NOTIFY_AT = range(3)

def get_db_session():
    """Helper to get a new DB session."""
    return SessionLocal()

def restricted_to_role(roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            chat_id = str(update.effective_chat.id)
            db_session = get_db_session()
            try:
                user = UserService.get_user_by_telegram_chat_id(db_session, chat_id)
                if not user:
                    await update.message.reply_text("Your account is not linked. Please use /start.")
                    return
                if user.role not in roles:
                    await update.message.reply_text("You are not authorized to use this command.")
                    return
                
                context.user_data['user_id'] = user.id
                return await func(update, context, *args, **kwargs)
            finally:
                db_session.close()
        return wrapper
    return decorator

async def start(update, context):
    chat_id = str(update.message.chat_id)
    telegram_username = update.effective_user.username
    args = context.args
    db_session = get_db_session()

    try:
        if args:
            token = args[0]
            user_id_bytes = redis_conn.get(f"telegram_token:{token}")

            if not user_id_bytes:
                await update.message.reply_text("This link is invalid or has expired.")
                return

            user_id = int(user_id_bytes.decode('utf-8'))
            
            existing_user = UserService.get_user_by_telegram_chat_id(db_session, chat_id)
            if existing_user and existing_user.id != user_id:
                await update.message.reply_text("This Telegram account is already linked to another user.")
                return

            user = UserService.get_user_by_id(db_session, user_id)
            if user:
                user.telegram_chat_id = chat_id
                user.telegram_username = telegram_username
                db_session.commit()
                redis_conn.delete(f"telegram_token:{token}")
                await update.message.reply_text(f"Success! Linked to profile '{user.username}'.")
            else:
                await update.message.reply_text("An error occurred: User not found.")
            return

        user = UserService.get_user_by_telegram_chat_id(db_session, chat_id)
        if user:
            await update.message.reply_text(f"This Telegram account is already linked to '{user.username}'.")
            return

        message = f"Welcome! To link this account, use the 'Connect with Telegram' button on your web profile.\n\nYour Chat ID is: `{chat_id}`"
        await update.message.reply_text(message, parse_mode='Markdown')
    finally:
        db_session.close()

@restricted_to_role([UserRole.USER, UserRole.ADMIN, UserRole.TRUSTED])
async def task_list(update, context):
    chat_id = update.message.chat_id
    command = update.message.text.split(" ")[0]
    task_type = command.split("_")[-1].upper()
    if task_type == "ALL":
        task_type = "all"
    q.enqueue('app.tasks_rq.handle_task_list', chat_id, task_type)
    await update.message.reply_text("Fetching your tasks...")

@restricted_to_role([UserRole.USER, UserRole.ADMIN, UserRole.TRUSTED])
async def task_delete(update, context):
    user_id = context.user_data['user_id']
    db_session = get_db_session()

    try:
        if not context.args:
            await update.message.reply_text("Usage: /task_delete <task_id>")
            return ConversationHandler.END

        task_id = int(context.args[0])
        task = TaskService.get_task(db_session, task_id)

        if not task or task.user_id != user_id:
            await update.message.reply_text("Task not found or you are not authorized.")
            return ConversationHandler.END

        context.user_data["task_to_delete"] = task.id
        context.user_data["task_title"] = task.title
        keyboard = [[InlineKeyboardButton("Yes", callback_data="delete_yes"), InlineKeyboardButton("No", callback_data="delete_no")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Delete task: {task.title}?", reply_markup=reply_markup)
        return CONFIRM_DELETE
    finally:
        db_session.close()

async def task_delete_confirm(update, context):
    query = update.callback_query
    await query.answer()
    user_id = context.user_data['user_id']
    task_id = context.user_data["task_to_delete"]
    task_title = context.user_data["task_title"]

    if query.data == "delete_yes":
        q.enqueue('app.tasks_rq.delete_task', user_id, task_id)
        await query.edit_message_text(text=f"Task '{task_title}' is being deleted.")
    else:
        await query.edit_message_text(text="Task deletion cancelled.")
    
    context.user_data.clear()
    return ConversationHandler.END

@restricted_to_role([UserRole.USER, UserRole.ADMIN, UserRole.TRUSTED])
async def add_task_start(update, context):
    command = update.message.text.split(" ")[0]
    task_type = command.split("_")[-1].upper()
    context.user_data["task_type"] = task_type
    await update.message.reply_text(f"Adding a new {task_type} task. What is the title?")
    return GET_TITLE

async def get_title(update, context):
    context.user_data["title"] = update.message.text
    keyboard = [[InlineKeyboardButton("Yes", callback_data="notify_yes"), InlineKeyboardButton("No", callback_data="notify_no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Set a notification?", reply_markup=reply_markup)
    return GET_NOTIFY_CHOICE

async def get_notify_choice(update, context):
    query = update.callback_query
    await query.answer()
    user_id = context.user_data['user_id']

    if query.data == "notify_yes":
        await query.edit_message_text(text="Provide notification time (YYYY-MM-DD HH:MM).")
        return GET_NOTIFY_AT
    else:
        task_data = TaskCreate(title=context.user_data["title"], type=context.user_data["task_type"])
        q.enqueue('app.tasks_rq.create_task', user_id, task_data.model_dump())
        await query.edit_message_text(text=f"Task '{context.user_data['title']}' created.")
        context.user_data.clear()
        return ConversationHandler.END

async def get_notify_at(update, context):
    user_id = context.user_data['user_id']
    try:
        notify_at = datetime.strptime(update.message.text, "%Y-%m-%d %H:%M")
        task_data = TaskCreate(title=context.user_data["title"], type=context.user_data["task_type"], notify_at=notify_at)
        q.enqueue('app.tasks_rq.create_task', user_id, task_data.model_dump())
        await update.message.reply_text(f"Task '{context.user_data['title']}' with notification created.")
    except ValueError:
        await update.message.reply_text("Invalid format. Please use YYYY-MM-DD HH:MM.")
        return GET_NOTIFY_AT
    context.user_data.clear()
    return ConversationHandler.END

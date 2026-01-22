import logging
from datetime import datetime
from functools import wraps

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

from app.models import User, UserRole, Task
from app.schemas import TaskCreate
from app.queue import q, redis_conn
from app.extensions import db


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CONFIRM_DELETE = 0
GET_TITLE, GET_NOTIFY_CHOICE, GET_NOTIFY_AT = range(3)


def restricted_to_role(roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            chat_id = update.effective_chat.id
            user = User.query.filter_by(telegram_chat_id=str(chat_id)).first()

            if not user:
                await update.message.reply_text("Your account is not linked. Please use /start to link your account.")
                return

            if user.role not in roles:
                role_value = user.role.value if user.role else "Not set"
                await update.message.reply_text(f"You are not authorized to use this command. Your role is {role_value}.")
                return

            context.user_data['user'] = user
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


async def start(update, context):
    chat_id = str(update.message.chat_id)
    telegram_username = update.effective_user.username
    args = context.args

    if args:
        token = args[0]
        user_id_bytes = redis_conn.get(f"telegram_token:{token}")

        if not user_id_bytes:
            await update.message.reply_text(
                "This link is invalid or has expired. Please generate a new one on the website's profile page."
            )
            return

        user_id = int(user_id_bytes.decode('utf-8'))

        # Check if this telegram account is already linked to someone else
        existing_user_with_chat_id = User.query.filter_by(telegram_chat_id=chat_id).first()
        if existing_user_with_chat_id and existing_user_with_chat_id.id != user_id:
            await update.message.reply_text(
                "This Telegram account is already linked to another user. "
                "Please unlink it from the other account before linking it to a new one."
            )
            return

        user = User.query.get(user_id)
        if user:
            user.telegram_chat_id = chat_id
            user.telegram_username = telegram_username
            db.session.commit()
            redis_conn.delete(f"telegram_token:{token}")
            await update.message.reply_text(
                f"Success! Your Telegram account is now linked to your profile '{user.username}'."
            )
        else:
            # This case should be rare if the token system is working correctly
            await update.message.reply_text("An error occurred: The user associated with this link could not be found.")
        return

    # Original start command logic if no token is provided
    user = User.query.filter_by(telegram_chat_id=chat_id).first()
    if user:
        await update.message.reply_text(
            f"This Telegram account is already linked to the user '{user.username}'. "
            f"You can manage your linked accounts on the web application's profile page."
        )
        return

    message = (
        f"Welcome! To link this Telegram account with your web profile, please do the following:\n\n"
        f"1. Log in to the web application.\n"
        f"2. Go to your profile page.\n"
        f"3. Click the 'Connect with Telegram' button.\n\n"
        f"Your Chat ID is: `{chat_id}` (You no longer need to enter this manually)."
    )
    await update.message.reply_text(message, parse_mode='Markdown')


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
    user = context.user_data['user']

    if not context.args:
        await update.message.reply_text("Please provide a task ID. Usage: /task_delete <task_id>")
        return ConversationHandler.END

    task_id = context.args[0]
    task = Task.query.get(task_id)

    if not task or task.user_id != user.id:
        await update.message.reply_text("Task not found or you are not authorized to delete it.")
        return ConversationHandler.END

    context.user_data["task_to_delete"] = task
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="delete_yes"),
            InlineKeyboardButton("No", callback_data="delete_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Are you sure you want to delete this task: {task.title}?",
        reply_markup=reply_markup,
    )
    return CONFIRM_DELETE


async def task_delete_confirm(update, context):
    query = update.callback_query
    await query.answer()
    user = context.user_data['user']
    task = context.user_data["task_to_delete"]

    if query.data == "delete_yes":
        q.enqueue('app.tasks_rq.delete_task', user.id, task.id)
        await query.edit_message_text(text=f"Task '{task.title}' is being deleted.")
    else:
        await query.edit_message_text(text="Task deletion cancelled.")

    del context.user_data["task_to_delete"]
    del context.user_data["user"]
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
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="notify_yes"),
            InlineKeyboardButton("No", callback_data="notify_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Do you want to set a notification for this task?", reply_markup=reply_markup
    )
    return GET_NOTIFY_CHOICE


async def get_notify_choice(update, context):
    query = update.callback_query
    await query.answer()
    user = context.user_data['user']

    if query.data == "notify_yes":
        await query.edit_message_text(text="Please provide the notification date and time in the format YYYY-MM-DD HH:MM.")
        return GET_NOTIFY_AT
    else:
        task_data = TaskCreate(
            title=context.user_data["title"],
            type=context.user_data["task_type"],
        )
        q.enqueue('app.tasks_rq.create_task', user.id, task_data.model_dump())
        await query.edit_message_text(text=f"Task '{context.user_data['title']}' is being created.")
        context.user_data.clear()
        return ConversationHandler.END


async def get_notify_at(update, context):
    user = context.user_data['user']
    try:
        notify_at = datetime.strptime(update.message.text, "%Y-%m-%d %H:%M")
        task_data = TaskCreate(
            title=context.user_data["title"],
            type=context.user_data["task_type"],
            notify_at=notify_at,
        )
        q.enqueue('app.tasks_rq.create_task', user.id, task_data.model_dump())
        await update.message.reply_text(text=f"Task '{context.user_data['title']}' with notification is being created.")
    except ValueError:
        await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD HH:MM.")
        return GET_NOTIFY_AT
    context.user_data.clear()
    return ConversationHandler.END

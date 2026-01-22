import logging
import asyncio
from telegram import Bot
from flask import current_app, Flask
from typing import Optional

logger = logging.getLogger(__name__)

async def send_telegram_message(chat_id: str, message: str, app_instance: Optional[Flask] = None):
    """
    Sends a Telegram message to a specified chat_id.
    Can accept a Flask app instance if called outside an existing app context.
    """
    token = None
    if app_instance:
        with app_instance.app_context():
            token = current_app.config.get("TELEGRAM_BOT_TOKEN")
    elif current_app:
        token = current_app.config.get("TELEGRAM_BOT_TOKEN")
    else:
        logger.error("No Flask app instance or current_app found to retrieve TELEGRAM_BOT_TOKEN.")
        return

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured. Cannot send Telegram message.")
        return

    try:
        bot = Bot(token=token)
        # Ensure this is awaited correctly in async contexts
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        logger.info(f"Telegram message sent to {chat_id}: {message}")
    except Exception as e:
        logger.error(f"Failed to send Telegram message to {chat_id}: {e}")

def run_async_in_new_loop(coro):
    """
    Runs an async coroutine in a new event loop.
    Useful for calling async functions from sync contexts.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError: # No running loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


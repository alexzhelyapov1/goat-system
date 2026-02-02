import logging
import asyncio
from telegram import Bot
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

async def send_telegram_message(chat_id: str, message: str):
    """
    Sends a Telegram message to a specified chat_id.
    """
    token = Config.TELEGRAM_BOT_TOKEN
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
        raise # Re-raise the exception to be handled by caller

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


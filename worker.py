import redis
from rq import Worker
from app.queue import q
from config import Config

from app import create_app
from app.models import User
from app.telegram_utils import send_telegram_message, run_async_in_new_loop
import traceback
import asyncio

# Create a Flask app instance for context within the worker
app = create_app()

def rq_exception_handler(job, exc_type, exc_value, traceback_obj):
    """
    Custom exception handler for RQ worker jobs.
    Sends error reports to 'alex' via Telegram.
    """
    with app.app_context():
        app.logger.error(f"RQ Job failed: {job.id}", exc_info=(exc_type, exc_value, traceback_obj))

        error_message = f"🚨 *RQ Job Failure (Worker Service)* 🚨\n\n" \
                        f"**Job ID:** `{job.id}`\n" \
                        f"**Task:** `{job.func_name}`\n" \
                        f"**Error Type:** `{exc_type.__name__}`\n" \
                        f"**Message:** `{exc_value}`\n" \
                        f"**Traceback:**\n```\n{''.join(traceback.format_exception(exc_type, exc_value, traceback_obj))}\n```"

        alex_user = User.query.filter_by(username='alex').first()
        if alex_user and alex_user.telegram_chat_id:
            try:
                run_async_in_new_loop(send_telegram_message(
                    chat_id=alex_user.telegram_chat_id,
                    message=error_message,
                    app_instance=app # Pass app instance for context
                ))
            except Exception as tg_e:
                app.logger.error(f"Failed to send Telegram error report from RQ handler: {tg_e}", exc_info=True)
        else:
            app.logger.warning("Could not find user 'alex' or their Telegram chat ID for RQ error reporting.")

def run_worker():
    redis_url = Config.REDIS_URL
    redis_connection = redis.from_url(redis_url)
    worker = Worker([q], connection=redis_connection, exception_handlers=[rq_exception_handler])
    worker.work()

if __name__ == '__main__':
    run_worker()

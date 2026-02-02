import redis
from rq import Worker
from config import Config
import logging
import traceback
from app.telegram_utils import send_telegram_message, run_async_in_new_loop
from app.queue import q

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def rq_exception_handler(job, exc_type, exc_value, traceback_obj):
    """
    Custom exception handler for RQ worker jobs.
    Sends error reports to the configured admin chat ID via Telegram.
    """
    logger.error(f"RQ Job failed: {job.id}", exc_info=(exc_type, exc_value, traceback_obj))

    error_message = f"🚨 *RQ Job Failure (Worker Service)* 🚨\n\n" \
                    f"**Job ID:** `{job.id}`\n" \
                    f"**Task:** `{job.func_name}`\n" \
                    f"**Error Type:** `{exc_type.__name__}`\n" \
                    f"**Message:** `{exc_value}`\n" \
                    f"**Traceback:**\n```\n{''.join(traceback.format_exception(exc_type, exc_value, traceback_obj))}\n```"

    admin_chat_id = Config.TELEGRAM_ADMIN_CHAT_ID
    if admin_chat_id:
        try:
            # run_async_in_new_loop is required because RQ handlers are sync
            run_async_in_new_loop(send_telegram_message(
                chat_id=admin_chat_id,
                message=error_message,
            ))
        except Exception as tg_e:
            logger.error(f"Failed to send Telegram error report from RQ handler: {tg_e}", exc_info=True)
    else:
        logger.warning("Could not send error report to admin: TELEGRAM_ADMIN_CHAT_ID not set.")

def run_worker():
    """Initializes and runs the RQ worker."""
    redis_url = Config.REDIS_URL
    redis_connection = redis.from_url(redis_url)
    
    # We pass the handler to the worker, not the queue
    worker = Worker([q], connection=redis_connection, exception_handlers=[rq_exception_handler])
    
    logger.info("Starting RQ worker...")
    worker.work(with_scheduler=True)

if __name__ == '__main__':
    run_worker()

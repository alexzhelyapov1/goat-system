import logging
from app import create_app
from app.scheduler import init_scheduler
import time

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting scheduler process...")
    app = create_app()
    with app.app_context():
        if not app.config.get('TESTING', False):
            init_scheduler(app)
        else:
            logger.info("Scheduler not started in TESTING mode.")

    # Keep the process alive
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()

import logging
from app.scheduler import init_scheduler
import time
from config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting scheduler process...")
    init_scheduler()
    # Keep the process alive
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()

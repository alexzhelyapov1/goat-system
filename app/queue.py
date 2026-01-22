import redis
from rq import Queue
from config import Config

redis_conn = redis.from_url(Config.REDIS_URL)
q = Queue('goat-system-tasks', connection=redis_conn)

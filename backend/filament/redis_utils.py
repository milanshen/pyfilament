import logging
import os

import redis
import redis.asyncio
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
REDIS_HOST = os.getenv('FILAMENT_REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('FILAMENT_REDIS_PORT', 6379)
REDIS_DB = os.getenv('FILAMENT_REDIS_DB', 0)


r = redis.asyncio.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
r_sync = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

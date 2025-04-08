import logging

import redis
import redis.asyncio
from dotenv import dotenv_values

logger = logging.getLogger(__name__)

dotenv_config = dotenv_values()
REDIS_HOST = dotenv_config.get('REDIS_HOST', 'localhost')
REDIS_PORT = dotenv_config.get('REDIS_PORT', 6379)
REDIS_DB = dotenv_config.get('REDIS_DB', 0)


r = redis.asyncio.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
r_sync = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

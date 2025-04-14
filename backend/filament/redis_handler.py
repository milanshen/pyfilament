import json
import logging
from datetime import datetime

import redis

logger = logging.getLogger(__name__)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_dict = {
            'timestamp': record.created,
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        return json.dumps(log_dict, default=str, separators=(',', ':'))


class RedisHandler(logging.Handler):
    def __init__(self, redis_host='localhost', redis_port=6379, key_prefix='filament_log', max_length=None):
        super().__init__()
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.key_prefix = key_prefix
        self.max_length = max_length

    def emit(self, record):
        try:
            msg = self.format(record)
            redis_key = f'{self.key_prefix}:{record.name}'
            self.redis.rpush(redis_key, msg)
            if self.max_length:
                self.redis.ltrim(redis_key, -self.max_length, -1)
            # logger.debug(f'Log message pushed to Redis list: {redis_key} {msg}')
        except Exception:
            self.handleError(record)

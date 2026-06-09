import logging
import time
from functools import partial

import anyio
from filament.redis.semaphore import RedisSemaphore, RedisSemaphoreException
from filament.redis.client import r


async def test_semaphore():
    async with anyio.create_task_group() as tg:
        for i in range(10):
            tg.start_soon(partial(_acquire_semaphore, seconds=i + 1))


async def _acquire_semaphore(seconds=3):
    try:
        semaphore = RedisSemaphore(redis=r, name='test', max_leases=2, ttl=5)
        start = time.time()
        logger = logging.getLogger(__name__)
        logger.info('Acquiring semaphore...')
        async with semaphore:
            acquired = time.time()
            logger.info(
                f'Semaphore acquired by {semaphore.client_id} in {acquired - start:.2f} seconds, holding for {seconds} seconds'
            )
            for i in range(seconds):
                await anyio.sleep(0.1)
                await semaphore.extend(1)
        end = time.time()
        logger.info(f'Semaphore released by {semaphore.client_id} after {end - acquired:.2f} seconds')
    except RedisSemaphoreException as e:
        logger.error(str(e))

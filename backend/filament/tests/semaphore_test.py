import logging
import time
from functools import partial

import anyio

from redis_semaphore import RedisSemaphore, RedisSemaphoreException
from redis_utils import r


async def main():
    async with anyio.create_task_group() as tg:
        for i in range(10):
            tg.start_soon(partial(acquire_semaphore, seconds=i + 1))


async def acquire_semaphore(seconds=3):
    try:
        semaphore = RedisSemaphore(redis=r, name="test", max_leases=2, ttl=5)
        start = time.time()
        logger = logging.getLogger(__name__)
        logger.info("Acquiring semaphore...")
        async with semaphore:
            acquired = time.time()
            logger.info(
                f"Semaphore acquired by {semaphore.client_id} in {acquired - start:.2f} seconds, holding for {seconds} seconds"
            )
            for i in range(seconds):
                await anyio.sleep(0.1)
                await semaphore.extend(1)
        end = time.time()
        logger.info(
            f"Semaphore released by {semaphore.client_id} after {end - acquired:.2f} seconds"
        )
    except RedisSemaphoreException as e:
        logger.error(str(e))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    anyio.run(main)

# import time
# import uuid

# import consul

# MAX_WORKERS = 4
# TTL_SECONDS = 15

# c = consul.Consul()
# worker_id = str(uuid.uuid4())
# session_id = c.session.create(name="worker", ttl=TTL_SECONDS, behavior="delete")
# key = f"semaphore/worker/{worker_id}"

# # Check current active workers
# _, kvs = c.kv.get("semaphore/worker/", recurse=True)
# active = len(kvs) if kvs else 0

# if active >= MAX_WORKERS:
#     print(f"Worker {worker_id[:8]} rejected")
#     c.session.destroy(session_id)
#     exit(1)

# # Try to acquire
# acquired = c.kv.put(key, "active", acquire=session_id)
# if not acquired:
#     print("Could not acquire lock")
#     c.session.destroy(session_id)
#     exit(1)

# print(f"Worker {worker_id[:8]} acquired lock")

# try:
#     while True:
#         c.session.renew(session_id)
#         time.sleep(TTL_SECONDS // 2)
# except KeyboardInterrupt:
#     print("Releasing lock...")
# finally:
#     c.session.destroy(session_id)

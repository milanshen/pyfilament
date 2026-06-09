from functools import partial

import anyio
from filament.redis.token_bucket import RedisTokenBucket


async def test_token_bucket():
    bucket = RedisTokenBucket(name='test_bucket', rate_limit=1, capacity=5)
    async with anyio.create_task_group() as tg:
        for i in range(5):
            tg.start_soon(partial(_acquire_tokens, num_tokens=i + 1, bucket=bucket))


async def _acquire_tokens(num_tokens=1, bucket=None):
    await bucket.acquire(tokens=num_tokens)
    print(f'Successfully acquired {num_tokens} tokens.')

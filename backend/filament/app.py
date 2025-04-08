import asyncio
import logging

import anyio

from filament import task


class CustomException(Exception):
    pass


@task(timeout=2.5, tries=2, delay=1.5, retry_exceptions=(CustomException, TimeoutError))
async def d(x):
    if x == 2:
        raise CustomException("Error in d")
    await asyncio.sleep(x)
    if x == 1:
        logger = d.get_logger()
        logger.info("hello from d")
        await f(x)
    return await f.request(x)


@task(cache=True)
async def f(x):
    return x**2


@task(max_concurrent=1)
async def g():
    await asyncio.sleep(10)


@task(rate_limit=1)
async def h():
    return


"""
four tasks:
1. succeeds after 1 second, calls child tasks, first success, second cached (1s), run counts = 1, 1, 0
2. fails immediately, delays for 1.5 seconds, fails again (1.5s), run count = 2
3. times out after 2.5 seconds (would've ran for 3), delays for 1.5 seconds, then times out again after 2.5 seconds (total 6.5s), run count = 2
4. canceled after 1.5 seconds. cancel monitor after an integer number of seconds, will cancel the task group (total 1.5-2.5s), run count = 1
"""


@task
async def root():
    print("Starting root task")
    tasks = [d(i + 1, start_immediately=True) for i in range(4)]
    await anyio.sleep(1.5)
    print("Cancelling last task")
    await tasks[-1].cancel()
    print("Waiting for tasks to finish")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"Results: {results}")
    # return results

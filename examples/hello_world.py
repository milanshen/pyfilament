import anyio

from filament.api.setup_logging import setup_logging
from filament.filament import get_logger, task

setup_logging()


@task
async def make_greeting():
    logger = get_logger()
    logger.info('Building greeting')
    await anyio.sleep(0.1)
    return 'world'


@task
async def say_hello():
    logger = get_logger()
    logger.info('Saying hello')
    await anyio.sleep(0.1)
    greeting = await make_greeting()
    await anyio.sleep(0.1)
    return f'Hello, {greeting}!'


async def main():
    result = await say_hello()
    print('result:', result)


if __name__ == '__main__':
    anyio.run(main)

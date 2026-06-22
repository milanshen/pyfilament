import asyncio
import logging

from .test_app import analyze_page, register_task_types

logging.getLogger().setLevel(logging.DEBUG)


async def main() -> None:
    # Register the task types, then serve analyze_page off the Redis queue until stopped.
    # Start as many workers as you like — they share the queue and the global
    # max_concurrent cap. Run from the repo root: python -m examples.web_analyst.worker
    await register_task_types()
    print('worker ready — serving analyze_page (submit jobs in another terminal)')
    await analyze_page.serve()


if __name__ == '__main__':
    asyncio.run(main())

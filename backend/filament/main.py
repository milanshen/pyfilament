import anyio
import fire

import setup_logging
from app import d, f, root
from filament import lookup

# from utils import print_task_run_registry


async def main():
    async with anyio.create_task_group() as task_group:
        task_group.start_soon(root.serve)
        task_group.start_soon(f.serve)
        task_group.start_soon(d.serve)
        await root.request()
        task_group.cancel_scope.cancel()


class Filament:
    def serve(self, task_address):
        anyio.run(lookup(task_address).serve)

    def request(self, task_address, count=1):
        async def _request():
            async with anyio.create_task_group() as task_group:
                for _ in range(count):
                    task_group.start_soon(lookup(task_address).request)

        anyio.run(_request)

    def call(self, task_address):
        async def _call():
            await lookup(task_address)()

        anyio.run(_call)


if __name__ == "__main__":
    # anyio.run(main)
    fire.Fire(Filament)

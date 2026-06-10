import anyio

from filament.filament import task


@task
async def _run_parent():
    await anyio.sleep(0.1)
    child_task = await _run_child.request()
    result = await child_task
    return f'parent, {result}'


@task
async def _run_child():
    await anyio.sleep(0.1)
    return 'child'


async def test_task():
    result = None

    async def _start_parent_task(cancel_scope: anyio.CancelScope):
        nonlocal result
        result = await _run_parent()
        cancel_scope.cancel()

    async with anyio.create_task_group() as tg:
        tg.start_soon(_run_child.serve)
        tg.start_soon(_start_parent_task, tg.cancel_scope)

    assert result == 'parent, child'

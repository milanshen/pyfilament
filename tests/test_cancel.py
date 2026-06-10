import anyio

from filament.filament import task

_global_state = {'parent_set': False, 'child_set': False}


@task
async def _run_parent():
    await anyio.sleep(0.1)
    _global_state['parent_set'] = True
    result = await _run_child()
    await anyio.sleep(0.1)
    return f'parent, {result}'


@task
async def _run_child():
    await anyio.sleep(0.1)
    _global_state['child_set'] = True
    return 'child'


async def test_cancel():
    parent_task = None

    async def _cancel_parent_task():
        nonlocal parent_task
        await anyio.sleep(0.15)
        assert parent_task is not None, 'Parent task not started'
        parent_task.cancel()

    async def _start_parent_task(cancel_scope: anyio.CancelScope):
        nonlocal parent_task
        parent_task = _run_parent()
        await parent_task
        cancel_scope.cancel()

    async with anyio.create_task_group() as tg:
        tg.start_soon(_start_parent_task, tg.cancel_scope)
        tg.start_soon(_cancel_parent_task)

    assert _global_state['parent_set']
    assert not _global_state['child_set']

from filament.filament import task
from filament.hooks import create_all_task_type_states
import anyio


@task
async def test_task_parent():
    await anyio.sleep(0.1)
    result = await test_task_child()
    await anyio.sleep(0.1)
    return f'parent, {result}'


@task
async def test_task_child():
    await anyio.sleep(0.1)
    return 'child'


async def test_task():
    await create_all_task_type_states()
    result = await test_task_parent()
    assert result == 'parent, child'

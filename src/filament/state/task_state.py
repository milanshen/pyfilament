import json
import logging
from typing import TYPE_CHECKING

from beartype import beartype
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from filament.db.models import TaskRun, TaskRunStateTransition, TaskType, get_utc_now
from filament.logic.utils import get_json_dict, json_encode_safe, redact_strings
from filament.state.common import with_session
from filament.task.constants import TaskState

if TYPE_CHECKING:
    from filament.task.types.task_run import FilamentTaskRun
else:
    FilamentTaskRun = 'filament.task.types.task_run.FilamentTaskRun'

logger = logging.getLogger(__name__)


@with_session
@beartype
async def set_heartbeat(session: AsyncSession, task_run: FilamentTaskRun) -> None:
    statement = select(TaskRun).where(TaskRun.task_uuid == task_run.uuid)
    task_run_row = (await session.execute(statement)).scalars().one()
    task_run_row.heartbeat = get_utc_now()


@with_session
@beartype
async def get_task_run_state(session: AsyncSession, task_uuid: str) -> TaskRun | None:
    statement = select(TaskRun).where(TaskRun.task_uuid == task_uuid)
    task_run_row = (await session.execute(statement)).scalars().one_or_none()
    return task_run_row


@with_session
@beartype
async def get_task_run_dict(session: AsyncSession, task_uuid: str) -> dict | None:
    task_run_row = await get_task_run_state(session, task_uuid)
    if task_run_row is not None:
        return get_json_dict(task_run_row)
    return None


@with_session
@beartype
async def create_task_run_state(
    session: AsyncSession,
    task_uuid: str,
    func_address: str,
    name: str | None = None,
    parameters: dict | None = None,
    is_redact: bool = False,
) -> None:
    statement = select(TaskType).where(TaskType.func_address == func_address)
    task_type = (await session.execute(statement)).scalars().one_or_none()
    if task_type is None:
        raise ValueError(f'No task type found for func_address {func_address}')
    task_run_row = TaskRun(name=name, task_uuid=task_uuid, task_type_id=task_type.id)
    encodable_parameters = json_encode_safe(parameters)
    if is_redact:
        encodable_parameters = redact_strings(encodable_parameters)
    if parameters is not None:
        task_run_row.parameters_json = json.dumps(encodable_parameters, separators=(',', ':'), default=str)
    session.add(task_run_row)


@with_session
@beartype
async def transition_state(session: AsyncSession, task_run: FilamentTaskRun, new_state: TaskState) -> None:
    statement = select(TaskRun).where(TaskRun.task_uuid == task_run.uuid)
    task_run_row = (await session.execute(statement)).scalars().one()
    old_state = task_run_row.state
    if old_state == new_state:
        return
    if new_state == TaskState.RUNNING:
        task_run_row.run_count += 1
    task_run_row.state = new_state
    task_run_row.state_since = get_utc_now()
    transition = TaskRunStateTransition(
        task_uuid=task_run.uuid, from_state=old_state, to_state=new_state, state_since=task_run_row.state_since
    )
    session.add(transition)


@with_session
@beartype
async def set_task_result(session: AsyncSession, task_run: FilamentTaskRun) -> None:
    statement = select(TaskRun).where(TaskRun.task_uuid == task_run.uuid)
    task_run_row = (await session.execute(statement)).scalars().one()
    encodable_result = json_encode_safe(task_run._result or task_run._exception)
    if task_run.config.is_redact_output:
        encodable_result = redact_strings(encodable_result)
    task_run_row.result_json = json.dumps(encodable_result, separators=(',', ':'), default=str)


@with_session
@beartype
async def is_canceled(session: AsyncSession, task_uuid: str) -> bool:
    statement = select(TaskRun).where(TaskRun.task_uuid == task_uuid)
    task_run_row = (await session.execute(statement)).scalars().one()
    return task_run_row.state == TaskState.CANCELLED


@with_session
@beartype
async def set_parent_task_uuid(session: AsyncSession, task_uuid: str, parent_task_uuid: str) -> None:
    statement = select(TaskRun).where(TaskRun.task_uuid == task_uuid)
    task_run_row = (await session.execute(statement)).scalars().one()
    task_run_row.parent_task_uuid = parent_task_uuid

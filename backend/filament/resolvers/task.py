import strawberry
from sqlmodel import select
from werkzeug.exceptions import BadRequest, NotFound

from filament.db_models import TaskRun as TaskRunModel
from filament.db_models import TaskState
from filament.db_models import TaskType as TaskTypeModel
from filament.task_state import transition_state
from filament.types.task import TaskRun, TaskType


async def get_task_run(self, info, id: strawberry.ID | None = None, task_uuid: str | None = None) -> TaskRun:
    session = info.context['session']
    if task_uuid is not None:
        statement = select(TaskRunModel).where(TaskRunModel.task_uuid == task_uuid)
    elif id is not None:
        statement = select(TaskRunModel).where(TaskRunModel.id == id)
    else:
        raise BadRequest('Either id or task_uuid must be provided')
    task_run = session.exec(statement).first()
    if not task_run:
        raise NotFound(f'TaskRun with UUID {task_uuid} not found')
    return task_run


async def get_task_type(self, info, id: strawberry.ID | None = None, func_address: str | None = None) -> TaskType:
    session = info.context['session']
    if func_address is not None:
        statement = select(TaskTypeModel).where(TaskTypeModel.func_address == func_address)
    elif id is not None:
        statement = select(TaskTypeModel).where(TaskTypeModel.id == id)
    else:
        raise BadRequest('Either id or func_address must be provided')
    task_type = session.exec(statement).first()
    if not task_type:
        raise NotFound(f'TaskType with func_address {func_address} not found')
    return task_type


async def get_task_types(self, info):
    session = info.context['session']
    statement = select(TaskTypeModel)
    task_types = session.exec(statement).all()
    return task_types


async def cancel_task_run(self, info, id: strawberry.ID | None = None, task_uuid: str | None = None) -> TaskRun:
    session = info.context['session']
    if task_uuid is not None:
        statement = select(TaskRunModel).where(TaskRunModel.task_uuid == task_uuid)
    elif id is not None:
        statement = select(TaskRunModel).where(TaskRunModel.id == id)
    else:
        raise BadRequest('Either id or task_uuid must be provided')
    task_run = session.exec(statement).first()
    if not task_run:
        raise NotFound(f'TaskRun with UUID {task_uuid} not found')
    _cancel_task_run(task_run)
    session.commit()
    return task_run


def _cancel_task_run(task_run: TaskRunModel) -> TaskRunModel:
    if task_run.state in TaskState.TERMINAL:
        return task_run
    transition_state(task_run.task_uuid, TaskState.CANCELLED)
    for child_task_run in task_run.child_tasks:
        _cancel_task_run(child_task_run)

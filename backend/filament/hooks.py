import logging

from filament.db_models import TaskRun
from filament.db_session import session_scope
from filament.logic.task_run import cancel_task_run
from filament.utils_call_stack import peek_task_run

logger = logging.getLogger(__name__)


def get_current_task_run():
    task_run = peek_task_run()
    if task_run is not None:
        return task_run
    raise RuntimeError('No task found in stack')


def cancel_task_run_by_uuid(task_uuid: str):
    with session_scope() as session:
        query = session.query(TaskRun).where(TaskRun.task_uuid == task_uuid)
        task_run = query.one_or_none()
        if task_run is not None:
            cancel_task_run(task_run)
        else:
            logger.warning(f'TaskRun with UUID {task_uuid} not found')

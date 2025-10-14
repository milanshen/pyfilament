import logging

import strawberry
from fastapi import Depends, FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from strawberry.extensions import SchemaExtension
from strawberry.fastapi import GraphQLRouter

import filament.resolvers.task as task_resolver

# from filament.setup_logging import setup_logging
from centauri.init.setup_logging import setup_logging
from filament.db_models import Base
from filament.db_session import session_scope
from filament.types.task import TaskRun, TaskType

setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI()


def get_session_from_request(request: Request):
    return request.state.session


async def get_context(
    session=Depends(get_session_from_request),
):
    return {
        'session': session,
    }


class SessionFlusher(SchemaExtension):
    def resolve(self, _next, root, info, *args, **kwargs):
        if (
            info.path is not None
            and info.path.key is not None
            and (info.path.key == 'id' or info.path.key.endswith('_id'))
        ):
            if isinstance(root, Base) and getattr(root, info.path.key, None) is None:
                if info.context is not None and 'session' in info.context:
                    info.context['session'].flush()
        return _next(root, info, *args, **kwargs)


@strawberry.type
class Query:
    get_task_run: TaskRun = strawberry.field(resolver=task_resolver.get_task_run)
    get_task_type: TaskType = strawberry.field(resolver=task_resolver.get_task_type)
    get_task_types: list[TaskType] = strawberry.field(resolver=task_resolver.get_task_types)
    get_task_runs: list[TaskRun] = strawberry.field(resolver=task_resolver.get_task_runs)


@strawberry.type
class Mutation:
    cancel_task_run: TaskRun = strawberry.field(resolver=task_resolver.cancel_task_run)
    run_task: TaskRun = strawberry.field(resolver=task_resolver.run_task)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[SessionFlusher],
)


@app.get('/tasks')
async def root():
    return {'message': 'Hello World'}


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        with session_scope() as session:
            request.state.session = session
            return await call_next(request)


app.add_middleware(SessionMiddleware)
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)
app.include_router(graphql_app, prefix='/graphql')

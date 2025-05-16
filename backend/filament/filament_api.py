import strawberry
from fastapi import FastAPI
from strawberry.extensions import SchemaExtension
from strawberry.fastapi import GraphQLRouter

import filament.resolvers.task as task_resolver
from filament.db_models import get_session
from filament.types.task import TaskRun, TaskType

app = FastAPI()


class SessionManagement(SchemaExtension):
    # gets run once per request
    def on_execute(self):
        if self.execution_context.context is None:
            self.execution_context.context = {}
        if 'session' in self.execution_context.context:
            yield
        else:
            with get_session() as session:
                self.execution_context.context['session'] = session
                yield

    # gets run once per nested resolver
    def resolve(self, _next, root, info, *args, **kwargs):
        result = _next(root, info, *args, **kwargs)
        # flush here so that ids are populated for session queries in nested resolvers
        info.context['session'].flush()
        return result


@strawberry.type
class Query:
    get_task_run: TaskRun = strawberry.field(resolver=task_resolver.get_task_run)
    get_task_type: TaskType = strawberry.field(resolver=task_resolver.get_task_type)
    get_task_types: list[TaskType] = strawberry.field(resolver=task_resolver.get_task_types)
    get_task_runs: list[TaskRun] = strawberry.field(resolver=task_resolver.get_task_runs)


@strawberry.type
class Mutation:
    cancel_task_run: TaskRun = strawberry.field(resolver=task_resolver.cancel_task_run)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[SessionManagement],
)


@app.get('/tasks')
async def root():
    return {'message': 'Hello World'}


graphql_app = GraphQLRouter(
    schema,
)
app.include_router(graphql_app, prefix='/graphql')

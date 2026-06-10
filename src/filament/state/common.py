import inspect
from functools import wraps

from beartype import beartype
from beartype.typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession

from filament.db.session import async_session_scope


@beartype
def with_session(func: Callable) -> Callable:
    assert inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func), 'Function must be asynchronous'

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if 'session' in kwargs and isinstance(kwargs['session'], AsyncSession):
            session = kwargs.pop('session')
            return await func(session, *args, **kwargs)
        if len(args) > 0 and isinstance(args[0], AsyncSession):
            session = args[0]
            args = args[1:]
            return await func(session, *args, **kwargs)
        else:
            async with async_session_scope() as session:
                return await func(session, *args, **kwargs)

    return wrapper

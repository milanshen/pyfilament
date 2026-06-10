import inspect
import logging

from beartype import beartype
from beartype.typing import Callable

logger = logging.getLogger(__name__)


@beartype
class EventManager:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event_name: str) -> Callable:

        @beartype
        def decorator(func: Callable):
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(func)
            return func

        return decorator

    async def trigger(self, event_name: str, *args, **kwargs) -> None:
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                if inspect.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)

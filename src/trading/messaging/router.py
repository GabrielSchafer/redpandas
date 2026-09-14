from typing import Callable

from ..events.envelope import Event

Handler = Callable[[Event], None]


class Router:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    def on(self, event_type: str) -> Callable[[Handler], Handler]:
        def decorator(func: Handler) -> Handler:
            self._handlers.setdefault(event_type, []).append(func)
            return func

        return decorator

    def dispatch(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            handler(event)

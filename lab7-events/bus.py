from typing import Callable, Dict, List

from schemas import PlatformEvent

Handler = Callable[[PlatformEvent], None]


class EventBus:
    """An in-memory event bus. Subscribe by event type, or "*" for every event."""

    def __init__(self) -> None:
        self._subs: Dict[str, List[Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subs.setdefault(event_type, []).append(handler)

    def publish(self, event: PlatformEvent) -> None:
        for handler in self._subs.get(event.type, []):
            handler(event)
        for handler in self._subs.get("*", []):
            handler(event)

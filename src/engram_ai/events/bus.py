import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

class EventBus:
    """Synchronous publish/subscribe event bus with fail-open semantics."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event_name: str, callback: Callable) -> None:
        self._subscribers[event_name].append(callback)

    def off(self, event_name: str, callback: Callable) -> None:
        try:
            self._subscribers[event_name].remove(callback)
        except ValueError:
            pass

    def emit(self, event_name: str, payload: Any) -> None:
        for callback in self._subscribers.get(event_name, []):
            try:
                payload_copy = (
                    payload.model_copy(deep=True)
                    if hasattr(payload, "model_copy")
                    else payload
                )
                callback(payload_copy)
            except Exception:
                logger.exception("EventBus subscriber failed for %s", event_name)

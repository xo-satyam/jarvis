"""Lightweight synchronous event bus.

Services never call each other directly. They publish and subscribe to events
so the system stays decoupled. Subscriber errors are isolated: one failing
handler must not break delivery to the others.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

Subscriber = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    """An immutable message passed through the :class:`EventBus`.

    Attributes:
        name: The event topic, e.g. ``"wakeword.detected"``.
        payload: Arbitrary structured data for subscribers.
    """

    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Synchronous publish/subscribe bus keyed by event name."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Subscriber]] = {}

    def subscribe(self, event_name: str, handler: Subscriber) -> None:
        """Register ``handler`` to be called for every ``event_name`` event."""
        self._subscribers.setdefault(event_name, []).append(handler)
        logger.debug("Subscribed %s to '%s'", getattr(handler, "__name__", handler), event_name)

    def unsubscribe(self, event_name: str, handler: Subscriber) -> None:
        """Remove a previously registered ``handler``. No-op if absent."""
        handlers = self._subscribers.get(event_name)
        if handlers and handler in handlers:
            handlers.remove(handler)

    def publish(self, event: Event) -> None:
        """Deliver ``event`` to all subscribers, isolating handler errors."""
        handlers = list(self._subscribers.get(event.name, ()))
        logger.debug("Publishing '%s' to %d subscriber(s)", event.name, len(handlers))
        for handler in handlers:
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - isolation is the whole point
                logger.exception("Subscriber for '%s' raised; continuing", event.name)

    def emit(self, name: str, **payload: Any) -> None:
        """Convenience helper to build and publish an :class:`Event`."""
        self.publish(Event(name=name, payload=payload))

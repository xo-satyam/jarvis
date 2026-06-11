"""Base class for single-responsibility services.

Every JARVIS subsystem (orb, wake word, STT, action engine, ...) is a Service.
Services receive the shared :class:`~jarvis.core.events.EventBus` and expose
``start``/``stop`` lifecycle hooks managed by the LifecycleManager.
"""

from __future__ import annotations

import logging
from abc import ABC

from .events import EventBus

logger = logging.getLogger(__name__)


class Service(ABC):
    """Abstract base for all services.

    Subclasses override :meth:`on_start` / :meth:`on_stop` rather than
    ``start``/``stop`` so lifecycle bookkeeping stays consistent.
    """

    #: Human-readable service name; defaults to the class name.
    name: str = "service"

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._running = False
        if self.name == "service":
            self.name = type(self).__name__

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        logger.info("Starting service: %s", self.name)
        self.on_start()
        self._running = True

    def stop(self) -> None:
        if not self._running:
            return
        logger.info("Stopping service: %s", self.name)
        self.on_stop()
        self._running = False

    # Hooks for subclasses -------------------------------------------------
    def on_start(self) -> None:
        """Called once when the service starts. Override as needed."""

    def on_stop(self) -> None:
        """Called once when the service stops. Override as needed."""

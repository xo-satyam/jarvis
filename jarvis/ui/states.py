"""Orb visual states and the event-driven state controller.

The controller is pure logic (no Qt) so it is fully unit-testable headless.
The PySide6 widget subscribes to OrbController state changes for rendering.
"""

from __future__ import annotations

import enum
import logging
from typing import Callable, List

from ..core.events import Event, EventBus

logger = logging.getLogger(__name__)


class OrbState(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    SUCCESS = "success"
    ERROR = "error"


StateListener = Callable[[OrbState], None]

# Event topic -> resulting orb state.
_EVENT_STATE_MAP = {
    "wakeword.detected": OrbState.LISTENING,
    "stt.transcript": OrbState.PROCESSING,
    "action.success": OrbState.SUCCESS,
    "action.error": OrbState.ERROR,
    "action.unmatched": OrbState.ERROR,
    "tts.speak": OrbState.SPEAKING,
    "orb.idle": OrbState.IDLE,
}


class OrbController:
    """Maps EventBus events to :class:`OrbState` transitions."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._state = OrbState.IDLE
        self._listeners: List[StateListener] = []
        for topic in _EVENT_STATE_MAP:
            bus.subscribe(topic, self._on_event)

    @property
    def state(self) -> OrbState:
        return self._state

    def add_listener(self, listener: StateListener) -> None:
        self._listeners.append(listener)

    def _on_event(self, event: Event) -> None:
        new_state = _EVENT_STATE_MAP.get(event.name)
        if new_state is not None:
            self._set_state(new_state)

    def _set_state(self, state: OrbState) -> None:
        if state == self._state:
            return
        logger.debug("Orb state: %s -> %s", self._state.value, state.value)
        self._state = state
        for listener in self._listeners:
            try:
                listener(state)
            except Exception:  # noqa: BLE001
                logger.exception("Orb state listener failed")

"""Wake word detection ('Jarvis').

Consumes 'audio.frame' events and emits 'wakeword.detected' when the wake word
is heard. Real backend: openWakeWord (fully offline, no key, no network).
Mock backend: a frame whose bytes start with the marker b'WAKE' triggers a
detection, so the pipeline is testable headless.

Target: <100ms detection latency.
"""

from __future__ import annotations

import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Optional

from ..core.events import Event, EventBus
from ..core.profiler import Profiler
from ..core.services import Service

logger = logging.getLogger(__name__)

_WAKE_BUDGET_MS = 100.0


class WakeWordBackend(ABC):
    """Abstract wake-word detector operating on raw PCM frames."""

    @abstractmethod
    def detect(self, frame: bytes) -> bool:
        """Return True if the wake word is detected in this frame."""


class MockWakeWordBackend(WakeWordBackend):
    """Triggers on frames that begin with b'WAKE'. Deterministic for tests."""

    def detect(self, frame: bytes) -> bool:
        return frame.startswith(b"WAKE")


class OpenWakeWordBackend(WakeWordBackend):
    """Offline wake-word detection via openWakeWord (imported lazily)."""

    def __init__(self, threshold: float = 0.5) -> None:
        from openwakeword.model import Model  # noqa: WPS433 - optional dep

        self._model = Model(wakeword_models=["alexa"], inference_framework="onnx")
        self._threshold = threshold

    def detect(self, frame: bytes) -> bool:
        import numpy as np  # noqa: WPS433

        samples = np.frombuffer(frame, dtype=np.int16)
        scores = self._model.predict(samples)
        return any(score >= self._threshold for score in scores.values())


def get_wakeword_backend() -> WakeWordBackend:
    choice = os.environ.get("JARVIS_WAKEWORD", "").strip().lower()
    if not choice:
        choice = "openwakeword" if sys.platform == "darwin" else "mock"
    if choice == "openwakeword":
        return OpenWakeWordBackend()
    if choice == "mock":
        return MockWakeWordBackend()
    raise ValueError(f"Unknown JARVIS_WAKEWORD: {choice!r}")


class WakeWordService(Service):
    """Listens to audio frames and announces wake-word detections."""

    name = "WakeWordService"

    def __init__(self, bus: EventBus, backend: Optional[WakeWordBackend] = None) -> None:
        super().__init__(bus)
        self._backend = backend or get_wakeword_backend()
        self._active = True

    def on_start(self) -> None:
        self.bus.subscribe("audio.frame", self._on_frame)

    def on_stop(self) -> None:
        self.bus.unsubscribe("audio.frame", self._on_frame)

    def set_active(self, active: bool) -> None:
        """Pause detection (e.g. while already listening to a command)."""
        self._active = active

    def _on_frame(self, event: Event) -> None:
        if not self._active:
            return
        frame = event.payload.get("frame", b"")
        with Profiler.measure("wakeword.detect", budget_ms=_WAKE_BUDGET_MS):
            detected = self._backend.detect(frame)
        if detected:
            logger.info("Wake word detected")
            self.bus.emit("wakeword.detected")

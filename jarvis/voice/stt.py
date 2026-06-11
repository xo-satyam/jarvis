"""Speech-to-text.

After wake-up, captures a short utterance and transcribes it, emitting
'stt.transcript' with the recognized text. Real backend: faster-whisper
(offline, no network). Mock backend: returns a preset transcript so the
pipeline is testable headless.

Target: <300ms.
"""

from __future__ import annotations

import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Optional

from ..core.events import EventBus
from ..core.profiler import Profiler
from ..core.services import Service

logger = logging.getLogger(__name__)

_STT_BUDGET_MS = 300.0


class STTBackend(ABC):
    """Abstract transcriber."""

    @abstractmethod
    def transcribe(self, audio: bytes) -> str:
        """Return recognized text for a chunk of 16kHz mono int16 PCM audio."""


class MockSTTBackend(STTBackend):
    """Returns a preset transcript. Settable by tests."""

    def __init__(self, transcript: str = "") -> None:
        self.transcript = transcript

    def transcribe(self, audio: bytes) -> str:
        return self.transcript


class WhisperBackend(STTBackend):
    """Offline STT via faster-whisper (imported lazily).

    'base.en' is chosen for low latency; configurable via JARVIS_WHISPER_MODEL.
    """

    def __init__(self) -> None:
        from faster_whisper import WhisperModel  # noqa: WPS433 - optional dep

        model_size = os.environ.get("JARVIS_WHISPER_MODEL", "base.en")
        # int8 on CPU keeps it fast and offline on Apple Silicon.
        self._model = WhisperModel(model_size, device="auto", compute_type="int8")

    def transcribe(self, audio: bytes) -> str:
        import numpy as np  # noqa: WPS433

        samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self._model.transcribe(samples, language="en", beam_size=1)
        return " ".join(seg.text.strip() for seg in segments).strip()


def get_stt_backend() -> STTBackend:
    choice = os.environ.get("JARVIS_STT", "").strip().lower()
    if not choice:
        choice = "whisper" if sys.platform == "darwin" else "mock"
    if choice == "whisper":
        return WhisperBackend()
    if choice == "mock":
        return MockSTTBackend()
    raise ValueError(f"Unknown JARVIS_STT: {choice!r}")


class STTService(Service):
    """Transcribes a captured utterance and emits the transcript."""

    name = "STTService"

    def __init__(self, bus: EventBus, backend: Optional[STTBackend] = None) -> None:
        super().__init__(bus)
        self._backend = backend or get_stt_backend()

    def transcribe(self, audio: bytes) -> str:
        """Transcribe ``audio`` and publish 'stt.transcript'. Returns the text."""
        with Profiler.measure("stt.transcribe", budget_ms=_STT_BUDGET_MS):
            text = self._backend.transcribe(audio)
        logger.info("Transcript: %r", text)
        self.bus.emit("stt.transcript", text=text)
        return text

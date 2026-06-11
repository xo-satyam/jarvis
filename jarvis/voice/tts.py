"""Text-to-speech.

Speaks responses. Non-blocking (runs in a background thread) and interruptible
(a new utterance cancels the current one). Real backend: macOS 'say' invoked
via subprocess with an argument list (no shell, so no command injection).
Fully offline. Mock backend records spoken text for tests.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from abc import ABC, abstractmethod
from typing import List, Optional

from ..core.events import Event, EventBus
from ..core.services import Service

logger = logging.getLogger(__name__)


class TTSBackend(ABC):
    """Abstract speech synthesizer."""

    @abstractmethod
    def speak(self, text: str) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...


class MockTTSBackend(TTSBackend):
    """Records spoken text instead of producing audio."""

    def __init__(self) -> None:
        self.spoken: List[str] = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)

    def stop(self) -> None:
        pass


class MacOSTTSBackend(TTSBackend):
    """Speaks via the macOS 'say' binary. No shell; offline; nothing to exploit."""

    def __init__(self) -> None:
        self._proc = None

    def speak(self, text: str) -> None:
        import subprocess  # noqa: WPS433

        self.stop()
        # Argument list (not a shell string): user/transcribed text can never
        # be interpreted as a command.
        self._proc = subprocess.Popen(["/usr/bin/say", "--", text])

    def stop(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None


def get_tts_backend() -> TTSBackend:
    choice = os.environ.get("JARVIS_TTS", "").strip().lower()
    if not choice:
        choice = "macos" if sys.platform == "darwin" else "mock"
    if choice == "macos":
        return MacOSTTSBackend()
    if choice == "mock":
        return MockTTSBackend()
    raise ValueError(f"Unknown JARVIS_TTS: {choice!r}")


class TTSService(Service):
    """Speaks responses non-blockingly; new speech interrupts the old."""

    name = "TTSService"

    def __init__(self, bus: EventBus, backend: Optional[TTSBackend] = None) -> None:
        super().__init__(bus)
        self._backend = backend or get_tts_backend()
        self._lock = threading.Lock()

    def on_start(self) -> None:
        self.bus.subscribe("tts.speak", self._on_speak)

    def on_stop(self) -> None:
        self.bus.unsubscribe("tts.speak", self._on_speak)
        self._backend.stop()

    def speak(self, text: str) -> None:
        if not text:
            return
        with self._lock:
            self._backend.stop()  # interrupt current speech
            self._backend.speak(text)

    def _on_speak(self, event: Event) -> None:
        self.speak(event.payload.get("text", ""))

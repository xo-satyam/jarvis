"""Microphone capture service.

Owns the audio stream and feeds raw PCM frames to subscribers (wake word, STT)
via the EventBus topic 'audio.frame'. The real backend uses sounddevice; the
mock backend produces silence so the pipeline runs headless.

Fully offline. No network access.
"""

from __future__ import annotations

import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from ..core.events import EventBus
from ..core.services import Service

logger = logging.getLogger(__name__)

# 16 kHz mono is what wake-word and Whisper models expect.
SAMPLE_RATE = 16000
FRAME_SAMPLES = 1280  # 80ms @ 16kHz, the openWakeWord chunk size

FrameCallback = Callable[[bytes], None]


class AudioBackend(ABC):
    """Abstract microphone source."""

    @abstractmethod
    def start(self, on_frame: FrameCallback) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...


class MockAudioBackend(AudioBackend):
    """Produces nothing on its own; tests push frames via feed()."""

    def __init__(self) -> None:
        self._on_frame: Optional[FrameCallback] = None
        self.started = False

    def start(self, on_frame: FrameCallback) -> None:
        self._on_frame = on_frame
        self.started = True

    def stop(self) -> None:
        self.started = False

    def feed(self, frame: bytes) -> None:
        """Test helper: inject a frame as if captured from the mic."""
        if self._on_frame is not None:
            self._on_frame(frame)


class SoundDeviceBackend(AudioBackend):
    """Real microphone capture via sounddevice (imported lazily)."""

    def __init__(self) -> None:
        self._stream = None

    def start(self, on_frame: FrameCallback) -> None:
        import sounddevice as sd  # noqa: WPS433 - optional dep

        def _callback(indata, frames, time_info, status):  # noqa: ANN001
            if status:
                logger.warning("Audio status: %s", status)
            on_frame(bytes(indata))

        self._stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=FRAME_SAMPLES,
            dtype="int16",
            channels=1,
            callback=_callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None


def get_audio_backend() -> AudioBackend:
    choice = os.environ.get("JARVIS_AUDIO", "").strip().lower()
    if not choice:
        choice = "sounddevice" if sys.platform == "darwin" else "mock"
    if choice == "sounddevice":
        return SoundDeviceBackend()
    if choice == "mock":
        return MockAudioBackend()
    raise ValueError(f"Unknown JARVIS_AUDIO: {choice!r}")


class AudioService(Service):
    """Captures audio frames and republishes them on the EventBus."""

    name = "AudioService"

    def __init__(self, bus: EventBus, backend: Optional[AudioBackend] = None) -> None:
        super().__init__(bus)
        self._backend = backend or get_audio_backend()

    def on_start(self) -> None:
        self._backend.start(self._emit_frame)

    def on_stop(self) -> None:
        self._backend.stop()

    def _emit_frame(self, frame: bytes) -> None:
        self.bus.emit("audio.frame", frame=frame)

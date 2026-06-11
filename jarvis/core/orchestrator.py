from __future__ import annotations

import logging
import struct
from typing import Optional

from ..actions.engine import ActionEngine
from ..core.events import Event, EventBus
from ..core.services import Service
from ..voice.stt import STTService
from ..voice.tts import TTSService
from ..voice.wakeword import WakeWordService

logger = logging.getLogger(__name__)

_FRAME_SAMPLES = 1280
_SILENCE_RMS_THRESHOLD = 500
_SILENCE_FRAME_LIMIT = 25
_MAX_FRAMES = 150


class Orchestrator(Service):
    """Coordinates wake word, STT, the action engine and TTS responses."""

    name = "Orchestrator"

    def __init__(
        self,
        bus: EventBus,
        engine: ActionEngine,
        stt: STTService,
        tts: TTSService,
        wakeword: Optional[WakeWordService] = None,
    ) -> None:
        super().__init__(bus)
        self._engine = engine
        self._stt = stt
        self._tts = tts
        self._wakeword = wakeword
        self._listening = False
        self._buffer: bytearray = bytearray()
        self._silent_frames = 0

    def on_start(self) -> None:
        self.bus.subscribe("wakeword.detected", self._on_wake)
        self.bus.subscribe("audio.frame", self._on_audio_frame)
        self.bus.subscribe("stt.transcript", self._on_transcript)

    def on_stop(self) -> None:
        self.bus.unsubscribe("wakeword.detected", self._on_wake)
        self.bus.unsubscribe("audio.frame", self._on_audio_frame)
        self.bus.unsubscribe("stt.transcript", self._on_transcript)

    # Flow ------------------------------------------------------------------
    def _on_wake(self, _event: Event) -> None:
        self._listening = True
        self._buffer = bytearray()
        self._silent_frames = 0
        if self._wakeword is not None:
            self._wakeword.set_active(False)
        self.bus.emit("orb.listening")

    def _on_audio_frame(self, event: Event) -> None:
        if not self._listening:
            return
        frame: bytes = event.payload.get("frame", b"")
        if not frame:
            return
        self._buffer.extend(frame)

        rms = _rms(frame)
        if rms < _SILENCE_RMS_THRESHOLD:
            self._silent_frames += 1
        else:
            self._silent_frames = 0

        if len(self._buffer) >= _MAX_FRAMES * _FRAME_SAMPLES * 2:
            self._finish_utterance()
        elif self._silent_frames >= _SILENCE_FRAME_LIMIT and len(self._buffer) > 0:
            self._silent_frames = 0
            self._finish_utterance()

    def _finish_utterance(self) -> None:
        audio = bytes(self._buffer)
        self._buffer = bytearray()
        self.capture_and_transcribe(audio)

    def capture_and_transcribe(self, audio: bytes) -> None:
        if not self._listening:
            return
        self._stt.transcribe(audio)

    def _on_transcript(self, event: Event) -> None:
        text = event.payload.get("text", "").strip()
        self._listening = False
        self._buffer = bytearray()
        self._silent_frames = 0
        if self._wakeword is not None:
            self._wakeword.set_active(True)
        if not text:
            self._respond("I didn't catch that.")
            self._idle()
            return
        handled = self._engine.handle(text)
        if not handled:
            self._respond("I can't do that yet.")
        self._idle()

    def _respond(self, text: str) -> None:
        self.bus.emit("tts.speak", text=text)

    def _idle(self) -> None:
        self.bus.emit("orb.idle")


def _rms(frame: bytes) -> float:
    samples = len(frame) // 2
    if samples == 0:
        return 0.0
    total = 0.0
    for i in range(samples):
        val = struct.unpack_from("<h", frame, i * 2)[0]
        total += val * val
    return (total / samples) ** 0.5

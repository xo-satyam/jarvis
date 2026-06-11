"""Conversation orchestrator: the interaction loop.

Drives the spec's flow:

    idle -> wake word -> listening -> understanding -> action -> response -> idle

It is pure coordination logic (no Qt, no hardware) so it is unit-testable with
mock voice services. It owns no audio buffering details; STTService.transcribe
is called with whatever utterance audio the audio layer captured.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..actions.engine import ActionEngine
from ..core.events import Event, EventBus
from ..core.services import Service
from ..voice.stt import STTService
from ..voice.tts import TTSService
from ..voice.wakeword import WakeWordService

logger = logging.getLogger(__name__)


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

    def on_start(self) -> None:
        self.bus.subscribe("wakeword.detected", self._on_wake)
        self.bus.subscribe("stt.transcript", self._on_transcript)

    def on_stop(self) -> None:
        self.bus.unsubscribe("wakeword.detected", self._on_wake)
        self.bus.unsubscribe("stt.transcript", self._on_transcript)

    # Flow ------------------------------------------------------------------
    def _on_wake(self, _event: Event) -> None:
        self._listening = True
        if self._wakeword is not None:
            self._wakeword.set_active(False)  # don't re-trigger mid-command
        self.bus.emit("orb.listening")

    def capture_and_transcribe(self, audio: bytes) -> None:
        """Called by the audio layer once an utterance has been captured."""
        if not self._listening:
            return
        self._stt.transcribe(audio)  # emits 'stt.transcript'

    def _on_transcript(self, event: Event) -> None:
        text = event.payload.get("text", "").strip()
        self._listening = False
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

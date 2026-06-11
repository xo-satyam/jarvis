"""Application composition root.

Wires the deterministic core (Phase 2) together with the voice foundation and
orb (Phase 1). Backends default to mock off-Mac and to real offline engines on
macOS, so this same object is used by tests and by the live app.
"""

from __future__ import annotations

import logging

from .actions import build_default_registry
from .actions.engine import ActionEngine
from .core.events import EventBus
from .core.lifecycle import LifecycleManager
from .core.orchestrator import Orchestrator
from .intent.matcher import IntentMatcher
from .ui.states import OrbController
from .voice.audio import AudioService
from .voice.stt import STTService
from .voice.tts import TTSService
from .voice.wakeword import WakeWordService

logger = logging.getLogger(__name__)


class JarvisApplication:
    """Top-level object owning the bus, services, lifecycle and orb state."""

    def __init__(self) -> None:
        self.bus = EventBus()
        self.lifecycle = LifecycleManager()

        # Deterministic core (Phase 2)
        self.registry = build_default_registry()
        self.matcher = IntentMatcher(self.registry)
        self.action_engine = ActionEngine(self.bus, self.matcher)

        # Voice foundation (Phase 1)
        self.audio = AudioService(self.bus)
        self.wakeword = WakeWordService(self.bus)
        self.stt = STTService(self.bus)
        self.tts = TTSService(self.bus)
        self.orchestrator = Orchestrator(
            self.bus, self.action_engine, self.stt, self.tts, self.wakeword
        )

        # Orb state (UI rendering subscribes to this)
        self.orb = OrbController(self.bus)

        # Lifecycle order: TTS and wake word before orchestrator; audio last so
        # frames only flow once everyone is subscribed.
        for service in (self.tts, self.wakeword, self.stt, self.orchestrator, self.audio):
            self.lifecycle.register(service)

    def start(self) -> None:
        self.lifecycle.start_all()

    def stop(self) -> None:
        self.lifecycle.stop_all()

    def command(self, phrase: str) -> bool:
        """Direct text-command entry point (bypasses voice; used by CLI/tests)."""
        return self.action_engine.handle(phrase)

"""End-to-end pipeline test with mock voice backends (headless).

Simulates: wake word -> capture utterance -> transcribe -> action -> orb state.
"""

from jarvis.actions.backend import MockBackend
from jarvis.actions.engine import ActionEngine
from jarvis.actions import build_default_registry
from jarvis.core.events import EventBus
from jarvis.core.orchestrator import Orchestrator
from jarvis.intent.matcher import IntentMatcher
from jarvis.ui.states import OrbController, OrbState
from jarvis.voice.stt import MockSTTBackend, STTService
from jarvis.voice.tts import MockTTSBackend, TTSService
from jarvis.voice.wakeword import MockWakeWordBackend, WakeWordService


def _build(transcript):
    bus = EventBus()
    backend = MockBackend()
    engine = ActionEngine(bus, IntentMatcher(build_default_registry()), backend=backend)
    stt = STTService(bus, backend=MockSTTBackend(transcript))
    tts = TTSService(bus, backend=MockTTSBackend())
    wake = WakeWordService(bus, backend=MockWakeWordBackend())
    orch = Orchestrator(bus, engine, stt, tts, wake)
    orb = OrbController(bus)
    for svc in (tts, wake, stt, orch):
        svc.start()
    return bus, backend, tts, orch, orb


def test_full_flow_executes_action():
    bus, backend, tts, orch, orb = _build("open chrome")
    bus.emit("wakeword.detected")
    assert orb.state == OrbState.LISTENING
    orch.capture_and_transcribe(b"utterance")
    # action executed via mock backend
    assert ("launch_app", ("Google Chrome",)) in backend.calls
    # ended back at idle
    assert orb.state == OrbState.IDLE


def test_unmatched_command_speaks_fallback():
    bus, backend, tts, orch, orb = _build("do a backflip")
    bus.emit("wakeword.detected")
    orch.capture_and_transcribe(b"utterance")
    assert tts._backend.spoken == ["I can't do that yet."]  # noqa: SLF001


def test_empty_transcript_handled():
    bus, backend, tts, orch, orb = _build("")
    bus.emit("wakeword.detected")
    orch.capture_and_transcribe(b"utterance")
    assert tts._backend.spoken == ["I didn't catch that."]  # noqa: SLF001
    assert orb.state == OrbState.IDLE

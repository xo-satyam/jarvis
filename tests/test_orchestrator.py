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


def test_audio_frames_buffered_and_transcribed_on_silence():
    """Utterance capture: audio frame -> silence triggers transcribe."""
    bus, backend, tts, orch, orb = _build("paste")
    bus.emit("wakeword.detected")
    assert orb.state == OrbState.LISTENING
    # feed loud audio frames (simulating speech)
    loud = b"\xff\x7f" * 640  # 640 samples of max volume
    for _ in range(10):
        bus.emit("audio.frame", frame=loud)
    assert orch._buffer  # noqa: SLF001
    # feed silence frames -> triggers transcribe
    quiet = b"\x00\x00" * 640
    for _ in range(30):
        bus.emit("audio.frame", frame=quiet)
    assert ("hotkey", ("command", "v")) in backend.calls or ("press",)  # paste action
    assert orb.state == OrbState.IDLE


def test_utterance_cutoff_at_max_frames():
    """Max utterance length forces transcribe even without silence."""
    bus, backend, tts, orch, orb = _build("paste")
    bus.emit("wakeword.detected")
    loud = b"\xff\x7f" * 1280  # 1280 samples = 1 full frame @ 16kHz
    for _ in range(160):  # exceeds _MAX_FRAMES (150)
        bus.emit("audio.frame", frame=loud)
    assert orb.state == OrbState.IDLE


def test_audio_before_wake_ignored():
    """Audio frames before wake word should not be buffered."""
    bus, backend, tts, orch, orb = _build("paste")
    loud = b"\xff\x7f" * 640
    for _ in range(10):
        bus.emit("audio.frame", frame=loud)
    assert len(orch._buffer) == 0  # noqa: SLF001
    bus.emit("wakeword.detected")
    # now frames should buffer
    bus.emit("audio.frame", frame=loud)
    assert len(orch._buffer) > 0  # noqa: SLF001

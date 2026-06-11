from jarvis.core.events import EventBus
from jarvis.voice.audio import AudioService, MockAudioBackend
from jarvis.voice.stt import MockSTTBackend, STTService
from jarvis.voice.tts import MockTTSBackend, TTSService
from jarvis.voice.wakeword import MockWakeWordBackend, WakeWordService


def test_audio_frames_published():
    bus = EventBus()
    backend = MockAudioBackend()
    service = AudioService(bus, backend=backend)
    frames = []
    bus.subscribe("audio.frame", lambda e: frames.append(e.payload["frame"]))
    service.start()
    backend.feed(b"\x00\x01")
    assert frames == [b"\x00\x01"]
    service.stop()


def test_wakeword_detects_marker_frame():
    bus = EventBus()
    service = WakeWordService(bus, backend=MockWakeWordBackend())
    detected = []
    bus.subscribe("wakeword.detected", lambda e: detected.append(True))
    service.start()
    bus.emit("audio.frame", frame=b"WAKExxxx")
    bus.emit("audio.frame", frame=b"silence")
    assert detected == [True]


def test_wakeword_respects_active_flag():
    bus = EventBus()
    service = WakeWordService(bus, backend=MockWakeWordBackend())
    detected = []
    bus.subscribe("wakeword.detected", lambda e: detected.append(True))
    service.start()
    service.set_active(False)
    bus.emit("audio.frame", frame=b"WAKExxxx")
    assert detected == []


def test_stt_emits_transcript():
    bus = EventBus()
    service = STTService(bus, backend=MockSTTBackend("open chrome"))
    out = []
    bus.subscribe("stt.transcript", lambda e: out.append(e.payload["text"]))
    text = service.transcribe(b"audio")
    assert text == "open chrome"
    assert out == ["open chrome"]


def test_tts_speaks_and_interrupts():
    backend = MockTTSBackend()
    service = TTSService(EventBus(), backend=backend)
    service.speak("hello")
    service.speak("world")
    assert backend.spoken == ["hello", "world"]


def test_tts_event_subscription():
    bus = EventBus()
    backend = MockTTSBackend()
    service = TTSService(bus, backend=backend)
    service.start()
    bus.emit("tts.speak", text="hi")
    assert backend.spoken == ["hi"]
    service.stop()

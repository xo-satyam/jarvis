from jarvis.core.events import EventBus
from jarvis.ui.states import OrbController, OrbState


def test_initial_state_is_idle():
    assert OrbController(EventBus()).state == OrbState.IDLE


def test_event_driven_transitions():
    bus = EventBus()
    orb = OrbController(bus)

    bus.emit("wakeword.detected")
    assert orb.state == OrbState.LISTENING

    bus.emit("stt.transcript", text="paste")
    assert orb.state == OrbState.PROCESSING

    bus.emit("action.success", action="paste")
    assert orb.state == OrbState.SUCCESS

    bus.emit("orb.idle")
    assert orb.state == OrbState.IDLE


def test_error_states():
    bus = EventBus()
    orb = OrbController(bus)
    bus.emit("action.error", action="x")
    assert orb.state == OrbState.ERROR


def test_listener_notified():
    bus = EventBus()
    orb = OrbController(bus)
    seen = []
    orb.add_listener(seen.append)
    bus.emit("wakeword.detected")
    assert seen == [OrbState.LISTENING]

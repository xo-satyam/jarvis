from jarvis.core.events import Event, EventBus


def test_publish_delivers_to_subscribers(bus):
    received = []
    bus.subscribe("ping", lambda e: received.append(e.payload))
    bus.emit("ping", value=1)
    assert received == [{"value": 1}]


def test_error_isolation(bus):
    seen = []

    def bad(_):
        raise RuntimeError("boom")

    def good(e):
        seen.append(e.name)

    bus.subscribe("topic", bad)
    bus.subscribe("topic", good)
    bus.publish(Event("topic"))
    assert seen == ["topic"]  # good handler still ran


def test_unsubscribe(bus):
    calls = []
    handler = lambda e: calls.append(1)
    bus.subscribe("t", handler)
    bus.unsubscribe("t", handler)
    bus.emit("t")
    assert calls == []

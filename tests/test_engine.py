def test_engine_invokes_backend_for_paste(engine, backend):
    handled = engine.handle("paste")
    assert handled is True
    assert ("hotkey", ("command", "v")) in backend.calls


def test_engine_types_text(engine, backend):
    handled = engine.handle("type hello world")
    assert handled is True
    assert ("type_text", ("hello world",)) in backend.calls


def test_engine_open_chrome_launches_app(engine, backend):
    engine.handle("open chrome")
    assert ("launch_app", ("Google Chrome",)) in backend.calls


def test_engine_unmatched_emits_event(engine, bus):
    events = []
    bus.subscribe("action.unmatched", lambda e: events.append(e.payload["phrase"]))
    handled = engine.handle("do a backflip")
    assert handled is False
    assert events == ["do a backflip"]


def test_engine_success_event(engine, bus):
    events = []
    bus.subscribe("action.success", lambda e: events.append(e.payload["action"]))
    engine.handle("copy")
    assert events == ["copy"]

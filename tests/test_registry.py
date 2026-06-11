import pytest

from jarvis.intent.registry import Action, ActionRegistry, Safety


def _noop(backend):
    pass


def test_register_and_lookup():
    reg = ActionRegistry()
    reg.register(Action("x", "desc", ["do x"], Safety.SAFE, _noop))
    assert reg.get("x").name == "x"
    assert reg.match_alias("do x").name == "x"


def test_duplicate_name_rejected():
    reg = ActionRegistry()
    reg.register(Action("x", "d", ["a"], Safety.SAFE, _noop))
    with pytest.raises(ValueError):
        reg.register(Action("x", "d", ["b"], Safety.SAFE, _noop))


def test_duplicate_alias_rejected():
    reg = ActionRegistry()
    reg.register(Action("x", "d", ["shared"], Safety.SAFE, _noop))
    with pytest.raises(ValueError):
        reg.register(Action("y", "d", ["shared"], Safety.SAFE, _noop))


def test_default_registry_has_core_actions(registry):
    names = {a.name for a in registry.all()}
    for expected in {"copy", "paste", "open_chrome", "switch_tab", "type_text"}:
        assert expected in names

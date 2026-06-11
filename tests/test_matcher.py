import pytest


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("open chrome", "open_chrome"),
        ("please open chrome", "open_chrome"),
        ("paste", "paste"),
        ("insert clipboard", "paste"),
        ("switch tab", "switch_tab"),
        ("press enter", "press_enter"),
        ("scroll down", "scroll_down"),
        ("open vs code", "open_vscode"),
    ],
)
def test_exact_aliases(matcher, phrase, expected):
    match = matcher.resolve(phrase)
    assert match is not None
    assert match.action.name == expected
    assert match.params == {}


def test_type_text_param_extraction(matcher):
    match = matcher.resolve("type hello world")
    assert match is not None
    assert match.action.name == "type_text"
    assert match.params == {"text": "hello world"}


def test_unmatched_returns_none(matcher):
    assert matcher.resolve("do a backflip") is None


def test_empty_returns_none(matcher):
    assert matcher.resolve("   ") is None

"""Window and tab management handlers (macOS shortcuts)."""

from __future__ import annotations

from .backend import Backend

_CMD = "command"
_CTRL = "ctrl"


def maximize_window(backend: Backend) -> None:
    # macOS 'zoom' via the green button has no global shortcut; ctrl+cmd+f
    # toggles fullscreen which is the closest deterministic equivalent.
    backend.hotkey(_CTRL, _CMD, "f")


def minimize_window(backend: Backend) -> None:
    backend.hotkey(_CMD, "m")


def close_window(backend: Backend) -> None:
    backend.hotkey(_CMD, "w")


def switch_tab(backend: Backend) -> None:
    backend.hotkey(_CTRL, "tab")


def new_tab(backend: Backend) -> None:
    backend.hotkey(_CMD, "t")

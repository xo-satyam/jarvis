"""Keyboard / clipboard-adjacent deterministic handlers."""

from __future__ import annotations

from .backend import Backend

# macOS uses the Command key for clipboard and edit shortcuts.
_CMD = "command"


def copy(backend: Backend) -> None:
    backend.hotkey(_CMD, "c")


def paste(backend: Backend) -> None:
    backend.hotkey(_CMD, "v")


def undo(backend: Backend) -> None:
    backend.hotkey(_CMD, "z")


def redo(backend: Backend) -> None:
    backend.hotkey(_CMD, "shift", "z")


def press_enter(backend: Backend) -> None:
    backend.press("enter")


def type_text(backend: Backend, text: str = "") -> None:
    if text:
        backend.type_text(text)

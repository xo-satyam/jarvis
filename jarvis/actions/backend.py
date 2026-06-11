"""Pluggable OS-control backends.

The deterministic handlers depend only on the :class:`Backend` interface. On
macOS the real backend drives the OS (keyboard, mouse, AppleScript). In CI /
tests the :class:`MockBackend` records calls instead, so everything is testable
without a GUI.

Select a backend with the ``JARVIS_BACKEND`` env var: ``mock`` (default off-Mac)
or ``macos``.
"""

from __future__ import annotations

import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import List, Tuple

logger = logging.getLogger(__name__)


class Backend(ABC):
    """Abstract OS-control surface used by all action handlers."""

    @abstractmethod
    def hotkey(self, *keys: str) -> None:
        """Press a key combination, e.g. ``hotkey('command', 'c')``."""

    @abstractmethod
    def press(self, key: str) -> None:
        """Press and release a single key, e.g. ``press('enter')``."""

    @abstractmethod
    def type_text(self, text: str) -> None:
        """Type a literal string."""

    @abstractmethod
    def scroll(self, amount: int) -> None:
        """Scroll vertically. Negative scrolls down."""

    @abstractmethod
    def launch_app(self, app_name: str) -> None:
        """Open/focus a native application by name."""


class MockBackend(Backend):
    """Records calls instead of touching the OS. Used by tests and CI."""

    def __init__(self) -> None:
        self.calls: List[Tuple[str, tuple]] = []

    def _record(self, name: str, *args: object) -> None:
        self.calls.append((name, args))
        logger.debug("MockBackend.%s%s", name, args)

    def hotkey(self, *keys: str) -> None:
        self._record("hotkey", *keys)

    def press(self, key: str) -> None:
        self._record("press", key)

    def type_text(self, text: str) -> None:
        self._record("type_text", text)

    def scroll(self, amount: int) -> None:
        self._record("scroll", amount)

    def launch_app(self, app_name: str) -> None:
        self._record("launch_app", app_name)


class MacOSBackend(Backend):
    """Real macOS backend using pyautogui and AppleScript (osascript).

    pyautogui is imported lazily so this module imports cleanly on Linux CI.
    """

    def __init__(self) -> None:
        import pyautogui  # noqa: WPS433 - lazy, macOS only

        self._gui = pyautogui
        self._gui.PAUSE = 0.0  # latency matters

    def hotkey(self, *keys: str) -> None:
        self._gui.hotkey(*keys)

    def press(self, key: str) -> None:
        self._gui.press(key)

    def type_text(self, text: str) -> None:
        self._gui.typewrite(text)

    def scroll(self, amount: int) -> None:
        self._gui.scroll(amount)

    def launch_app(self, app_name: str) -> None:
        import subprocess  # noqa: WPS433

        subprocess.run(["open", "-a", app_name], check=False)


def get_backend() -> Backend:
    """Return a backend chosen by ``JARVIS_BACKEND`` (or platform default)."""
    choice = os.environ.get("JARVIS_BACKEND", "").strip().lower()
    if not choice:
        choice = "macos" if sys.platform == "darwin" else "mock"
    if choice == "macos":
        return MacOSBackend()
    if choice == "mock":
        return MockBackend()
    raise ValueError(f"Unknown JARVIS_BACKEND: {choice!r}")

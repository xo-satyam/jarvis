"""Mouse / scrolling deterministic handlers."""

from __future__ import annotations

from .backend import Backend

_SCROLL_STEP = 500


def scroll_down(backend: Backend) -> None:
    backend.scroll(-_SCROLL_STEP)


def scroll_up(backend: Backend) -> None:
    backend.scroll(_SCROLL_STEP)

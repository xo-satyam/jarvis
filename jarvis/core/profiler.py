"""Latency measurement utilities.

Latency destroys the JARVIS 'magic', so the spec sets hard targets
(intent resolution <50ms, action execution <100ms). The Profiler provides a
context manager and a decorator to measure and log timings against those
targets.
"""

from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from typing import Callable, Iterator, Optional, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., object])


class Profiler:
    """Measures elapsed time for a labelled block of work."""

    @staticmethod
    @contextmanager
    def measure(label: str, budget_ms: Optional[float] = None) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if budget_ms is not None and elapsed_ms > budget_ms:
                logger.warning("%s took %.2fms (budget %.0fms EXCEEDED)", label, elapsed_ms, budget_ms)
            else:
                logger.debug("%s took %.2fms", label, elapsed_ms)


def profile(label: Optional[str] = None, budget_ms: Optional[float] = None) -> Callable[[F], F]:
    """Decorator that times a function via :class:`Profiler`."""

    def decorator(func: F) -> F:
        tag = label or func.__name__

        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            with Profiler.measure(tag, budget_ms):
                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator

"""Application composition root.

Wires the deterministic core together. Voice, vision and the orb UI are
scaffolded (Phase 1/3) and not started here yet.
"""

from __future__ import annotations

import logging

from .actions import build_default_registry
from .actions.engine import ActionEngine
from .core.events import EventBus
from .core.lifecycle import LifecycleManager
from .intent.matcher import IntentMatcher

logger = logging.getLogger(__name__)


class JarvisApplication:
    """Top-level object owning the bus, services and lifecycle."""

    def __init__(self) -> None:
        self.bus = EventBus()
        self.lifecycle = LifecycleManager()
        self.registry = build_default_registry()
        self.matcher = IntentMatcher(self.registry)
        self.action_engine = self.lifecycle.register(
            ActionEngine(self.bus, self.matcher)
        )

    def start(self) -> None:
        self.lifecycle.start_all()

    def stop(self) -> None:
        self.lifecycle.stop_all()

    def command(self, phrase: str) -> bool:
        """Entry point for a recognized command phrase."""
        return self.action_engine.handle(phrase)

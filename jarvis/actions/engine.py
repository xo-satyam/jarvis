"""The ActionEngine: deterministic execution of resolved intents.

Given a phrase, it resolves an action via the :class:`IntentMatcher` and runs
the handler against the active :class:`Backend`. Results are published on the
EventBus so the orb can reflect success/error state. No LLM is involved.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..core.events import EventBus
from ..core.profiler import Profiler
from ..core.services import Service
from ..intent.matcher import IntentMatcher, Match
from .backend import Backend, get_backend

logger = logging.getLogger(__name__)

_ACTION_BUDGET_MS = 100.0


class ActionEngine(Service):
    """Resolves and executes deterministic actions."""

    name = "ActionEngine"

    def __init__(
        self,
        bus: EventBus,
        matcher: IntentMatcher,
        backend: Optional[Backend] = None,
    ) -> None:
        super().__init__(bus)
        self._matcher = matcher
        self._backend = backend or get_backend()

    def handle(self, phrase: str) -> bool:
        """Resolve ``phrase`` and execute it. Returns True if handled."""
        match = self._matcher.resolve(phrase)
        if match is None:
            self.bus.emit("action.unmatched", phrase=phrase)
            return False
        return self._execute(match)

    def _execute(self, match: Match) -> bool:
        action = match.action
        try:
            with Profiler.measure(f"action.{action.name}", budget_ms=_ACTION_BUDGET_MS):
                action.handler(self._backend, **match.params)
            self.bus.emit("action.success", action=action.name, params=match.params)
            return True
        except Exception:  # noqa: BLE001
            logger.exception("Action '%s' failed", action.name)
            self.bus.emit("action.error", action=action.name)
            return False

"""Deterministic intent matcher.

Maps a spoken phrase to a registered :class:`~jarvis.intent.registry.Action`
using normalized alias matching only. There is NO LLM in this path: resolution
must complete well under the 50ms budget.

Matching strategy (in order):
1. Exact normalized alias match.
2. Prefix match where the phrase starts with a parameterized alias
   (e.g. ``type hello world`` -> ``type`` + param ``text='hello world'``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from ..core.profiler import Profiler
from .aliases import normalize
from .registry import Action, ActionRegistry

logger = logging.getLogger(__name__)

_INTENT_BUDGET_MS = 50.0


@dataclass
class Match:
    """Result of resolving a phrase."""

    action: Action
    params: Dict[str, str] = field(default_factory=dict)


class IntentMatcher:
    """Resolves phrases to actions deterministically."""

    def __init__(self, registry: ActionRegistry) -> None:
        self._registry = registry

    def resolve(self, phrase: str) -> Optional[Match]:
        with Profiler.measure("intent.resolve", budget_ms=_INTENT_BUDGET_MS):
            return self._resolve(phrase)

    def _resolve(self, phrase: str) -> Optional[Match]:
        normalized = normalize(phrase)
        if not normalized:
            return None

        # 1. Exact alias match.
        action = self._registry.match_alias(normalized)
        if action is not None:
            return Match(action=action)

        # 2. Parameterized prefix match. Longest alias first so 'type text'
        #    wins over 'type' when both are present.
        for alias_key, action in sorted(
            self._registry.aliases.items(), key=lambda kv: len(kv[0]), reverse=True
        ):
            if not action.parameters:
                continue
            prefix = alias_key + " "
            if normalized.startswith(prefix):
                remainder = normalized[len(prefix):].strip()
                param_name = action.parameters[0]
                return Match(action=action, params={param_name: remainder})

        logger.debug("No deterministic match for '%s'", phrase)
        return None

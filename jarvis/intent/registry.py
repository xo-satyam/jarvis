"""Action definitions and the registry that indexes them by alias."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .aliases import normalize

logger = logging.getLogger(__name__)


class Safety(enum.Enum):
    """How cautious JARVIS should be before executing an action."""

    SAFE = "safe"
    SENSITIVE = "sensitive"


@dataclass
class Action:
    """A deterministic, predefined operation.

    Attributes:
        name: Canonical unique action name.
        description: Human-readable description.
        aliases: Spoken phrases that map to this action.
        safety: Safety level (safe vs sensitive).
        handler: Callable invoked as ``handler(backend, **params)``.
        parameters: Names of params the handler accepts (e.g. ``["text"]``).
    """

    name: str
    description: str
    aliases: List[str]
    safety: Safety
    handler: Callable[..., None]
    parameters: List[str] = field(default_factory=list)


class ActionRegistry:
    """Stores actions and indexes their normalized aliases for fast lookup."""

    def __init__(self) -> None:
        self._actions: Dict[str, Action] = {}
        self._alias_index: Dict[str, Action] = {}

    def register(self, action: Action) -> None:
        if action.name in self._actions:
            raise ValueError(f"Duplicate action name: {action.name}")
        self._actions[action.name] = action
        for alias in action.aliases:
            key = normalize(alias)
            if key in self._alias_index:
                raise ValueError(
                    f"Alias '{alias}' already maps to '{self._alias_index[key].name}'"
                )
            self._alias_index[key] = action
        logger.debug("Registered action '%s' with %d alias(es)", action.name, len(action.aliases))

    def get(self, name: str) -> Optional[Action]:
        return self._actions.get(name)

    def match_alias(self, normalized_phrase: str) -> Optional[Action]:
        return self._alias_index.get(normalized_phrase)

    @property
    def aliases(self) -> Dict[str, Action]:
        return dict(self._alias_index)

    def all(self) -> List[Action]:
        return list(self._actions.values())

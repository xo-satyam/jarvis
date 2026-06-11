"""Deterministic intent resolution (no LLM)."""

from .registry import Action, ActionRegistry, Safety
from .matcher import IntentMatcher, Match

__all__ = ["Action", "ActionRegistry", "Safety", "IntentMatcher", "Match"]

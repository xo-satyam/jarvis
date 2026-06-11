"""Phrase normalization helpers shared by the registry and matcher."""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")
# Filler words a user might say that should not affect matching.
_FILLERS = {"please", "the", "a", "an"}


def normalize(phrase: str) -> str:
    """Lowercase, strip punctuation/extra whitespace, drop filler words."""
    text = phrase.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    tokens = [t for t in _WS.split(text) if t and t not in _FILLERS]
    return " ".join(tokens)

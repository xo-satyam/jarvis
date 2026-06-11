"""Orb visual states."""

from __future__ import annotations

import enum


class OrbState(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    SUCCESS = "success"
    ERROR = "error"

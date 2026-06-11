"""Deterministic computer-control actions.

Actions never use an LLM. They are predefined blocks of code executed
immediately. All OS interaction goes through a pluggable :class:`Backend` so
the engine runs headless in CI via the mock backend.
"""

from .backend import Backend, MockBackend, MacOSBackend, get_backend
from .registry_setup import build_default_registry

__all__ = [
    "Backend",
    "MockBackend",
    "MacOSBackend",
    "get_backend",
    "build_default_registry",
]

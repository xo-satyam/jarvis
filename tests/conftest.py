"""Shared test fixtures. Forces the mock backend for headless runs."""

import os

import pytest

os.environ.setdefault("JARVIS_BACKEND", "mock")

from jarvis.actions import build_default_registry
from jarvis.actions.backend import MockBackend
from jarvis.actions.engine import ActionEngine
from jarvis.core.events import EventBus
from jarvis.intent.matcher import IntentMatcher


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def registry():
    return build_default_registry()


@pytest.fixture
def matcher(registry):
    return IntentMatcher(registry)


@pytest.fixture
def backend():
    return MockBackend()


@pytest.fixture
def engine(bus, matcher, backend):
    return ActionEngine(bus, matcher, backend=backend)

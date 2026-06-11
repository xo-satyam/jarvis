"""Ordered startup/shutdown of services."""

from __future__ import annotations

import logging
from typing import List

from .services import Service

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Starts services in registration order and stops them in reverse."""

    def __init__(self) -> None:
        self._services: List[Service] = []

    def register(self, service: Service) -> Service:
        self._services.append(service)
        return service

    def start_all(self) -> None:
        for service in self._services:
            service.start()

    def stop_all(self) -> None:
        for service in reversed(self._services):
            try:
                service.stop()
            except Exception:  # noqa: BLE001
                logger.exception("Error stopping %s", service.name)

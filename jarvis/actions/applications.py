"""Application launch handlers."""

from __future__ import annotations

from .backend import Backend


def open_chrome(backend: Backend) -> None:
    backend.launch_app("Google Chrome")


def open_vscode(backend: Backend) -> None:
    backend.launch_app("Visual Studio Code")

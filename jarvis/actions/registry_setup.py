"""Wire the deterministic handlers into an :class:`ActionRegistry`."""

from __future__ import annotations

from ..intent.registry import Action, ActionRegistry, Safety
from . import applications, keyboard, mouse, windows


def build_default_registry() -> ActionRegistry:
    """Return a registry populated with all built-in deterministic actions."""
    registry = ActionRegistry()

    registry.register(Action(
        name="copy", description="Copy the current selection",
        aliases=["copy"], safety=Safety.SAFE, handler=keyboard.copy,
    ))
    registry.register(Action(
        name="paste", description="Paste clipboard contents",
        aliases=["paste", "insert clipboard"], safety=Safety.SAFE, handler=keyboard.paste,
    ))
    registry.register(Action(
        name="undo", description="Undo the last action",
        aliases=["undo"], safety=Safety.SAFE, handler=keyboard.undo,
    ))
    registry.register(Action(
        name="redo", description="Redo the last undone action",
        aliases=["redo"], safety=Safety.SAFE, handler=keyboard.redo,
    ))
    registry.register(Action(
        name="press_enter", description="Press the Enter key",
        aliases=["press enter", "hit enter", "return"], safety=Safety.SAFE,
        handler=keyboard.press_enter,
    ))
    registry.register(Action(
        name="type_text", description="Type the given text",
        aliases=["type", "type text", "write"], safety=Safety.SAFE,
        parameters=["text"], handler=keyboard.type_text,
    ))
    registry.register(Action(
        name="scroll_down", description="Scroll down",
        aliases=["scroll down"], safety=Safety.SAFE, handler=mouse.scroll_down,
    ))
    registry.register(Action(
        name="scroll_up", description="Scroll up",
        aliases=["scroll up"], safety=Safety.SAFE, handler=mouse.scroll_up,
    ))
    registry.register(Action(
        name="open_chrome", description="Open Google Chrome",
        aliases=["open chrome", "launch chrome"], safety=Safety.SAFE,
        handler=applications.open_chrome,
    ))
    registry.register(Action(
        name="open_vscode", description="Open Visual Studio Code",
        aliases=["open vscode", "open vs code", "open code", "launch vscode"],
        safety=Safety.SAFE, handler=applications.open_vscode,
    ))
    registry.register(Action(
        name="maximize_window", description="Maximize / fullscreen the window",
        aliases=["maximize window", "maximize", "fullscreen"], safety=Safety.SAFE,
        handler=windows.maximize_window,
    ))
    registry.register(Action(
        name="minimize_window", description="Minimize the window",
        aliases=["minimize window", "minimize"], safety=Safety.SAFE,
        handler=windows.minimize_window,
    ))
    registry.register(Action(
        name="close_window", description="Close the current window",
        aliases=["close window", "close"], safety=Safety.SENSITIVE,
        handler=windows.close_window,
    ))
    registry.register(Action(
        name="switch_tab", description="Switch to the next tab",
        aliases=["switch tab", "next tab"], safety=Safety.SAFE,
        handler=windows.switch_tab,
    ))
    registry.register(Action(
        name="new_tab", description="Open a new tab",
        aliases=["new tab"], safety=Safety.SAFE, handler=windows.new_tab,
    ))

    return registry

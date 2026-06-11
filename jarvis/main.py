"""CLI entry point.

For now this exposes the deterministic engine over stdin so the core can be
exercised without voice/orb. ``python -m jarvis.main`` then type commands.
"""

from __future__ import annotations

import logging

from .app import JarvisApplication


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = JarvisApplication()
    app.start()
    print("JARVIS V2 deterministic core. Type a command (Ctrl-D to exit).")
    try:
        while True:
            try:
                phrase = input("> ").strip()
            except EOFError:
                break
            if not phrase:
                continue
            handled = app.command(phrase)
            print("ok" if handled else "unrecognized")
    finally:
        app.stop()


if __name__ == "__main__":
    main()

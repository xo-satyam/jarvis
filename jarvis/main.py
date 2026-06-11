"""CLI / GUI entry point.

Without flags this runs a text REPL against the deterministic engine (works
headless, no mic/GUI). With ``--gui`` it launches the PySide6 orb (macOS), which
reacts to the live voice pipeline.

    python -m jarvis.main            # text REPL
    python -m jarvis.main --gui      # orb + voice (macOS)
"""

from __future__ import annotations

import argparse
import logging

from .app import JarvisApplication


def _run_repl(app: JarvisApplication) -> None:
    print("JARVIS V2 deterministic core. Type a command (Ctrl-D to exit).")
    while True:
        try:
            phrase = input("> ").strip()
        except EOFError:
            break
        if not phrase:
            continue
        print("ok" if app.command(phrase) else "unrecognized")


def _run_gui(app: JarvisApplication) -> None:
    from PySide6 import QtWidgets  # noqa: WPS433 - macOS runtime only

    from .ui.orb import create_orb_widget

    qt_app = QtWidgets.QApplication([])
    orb = create_orb_widget(app.orb)
    orb.show()
    qt_app.exec()


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS V2")
    parser.add_argument("--gui", action="store_true", help="Launch the orb (macOS).")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    app = JarvisApplication()
    app.start()
    try:
        if args.gui:
            _run_gui(app)
        else:
            _run_repl(app)
    finally:
        app.stop()


if __name__ == "__main__":
    main()

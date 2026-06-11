"""The orb window (PySide6).

A borderless, transparent, always-on-top, draggable orb that reflects
:class:`OrbState`. Qt is imported lazily so the rest of the package (and the
headless test suite) never depends on PySide6 being installed.

Colors per state follow the spec: idle (subtle), listening (blue glow),
processing (energy), speaking (pulse), success (green), error (red).
"""

from __future__ import annotations

import logging

from .states import OrbController, OrbState

logger = logging.getLogger(__name__)

_STATE_COLOR = {
    OrbState.IDLE: (90, 110, 140),
    OrbState.LISTENING: (40, 140, 255),
    OrbState.PROCESSING: (120, 90, 255),
    OrbState.SPEAKING: (40, 200, 220),
    OrbState.SUCCESS: (60, 200, 110),
    OrbState.ERROR: (220, 70, 70),
}


def create_orb_widget(controller: OrbController):
    """Construct and return the orb QWidget. Requires PySide6 (macOS runtime).

    Imported lazily; call only from the GUI process.
    """
    from PySide6 import QtCore, QtGui, QtWidgets  # noqa: WPS433

    class Orb(QtWidgets.QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint
                | QtCore.Qt.WindowStaysOnTopHint
                | QtCore.Qt.Tool
            )
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            self.resize(96, 96)
            self._state = OrbState.IDLE
            self._drag_offset = None
            controller.add_listener(self._on_state)

            # ~60 FPS animation tick for the breathing/pulse effect.
            self._phase = 0.0
            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(self._tick)
            self._timer.start(16)

        def _on_state(self, state: OrbState) -> None:
            self._state = state
            self.update()

        def _tick(self) -> None:
            self._phase = (self._phase + 0.05) % (2 * 3.14159)
            self.update()

        def paintEvent(self, _event) -> None:  # noqa: N802
            import math

            r, g, b = _STATE_COLOR.get(self._state, _STATE_COLOR[OrbState.IDLE])
            pulse = 0.5 + 0.5 * math.sin(self._phase)
            radius = 30 + 6 * pulse
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            center = self.rect().center()
            gradient = QtGui.QRadialGradient(center, radius)
            gradient.setColorAt(0.0, QtGui.QColor(r, g, b, 230))
            gradient.setColorAt(1.0, QtGui.QColor(r, g, b, 0))
            painter.setBrush(QtGui.QBrush(gradient))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(center, radius, radius)

        # Dragging ----------------------------------------------------------
        def mousePressEvent(self, event) -> None:  # noqa: N802
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

        def mouseMoveEvent(self, event) -> None:  # noqa: N802
            if self._drag_offset is not None:
                self.move(event.globalPosition().toPoint() - self._drag_offset)

        def mouseReleaseEvent(self, _event) -> None:  # noqa: N802
            self._drag_offset = None

    return Orb()

"""Wake word detection (Phase 1, not yet implemented).

Responsibility: continuously listen for 'Jarvis' and emit
'wakeword.detected' on the EventBus. Target: <100ms detection.
"""

from __future__ import annotations

# TODO(phase-1): integrate an on-device wake-word engine (e.g. openWakeWord).

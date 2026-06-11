"""Phase 1 - Voice foundation.

All engines run fully offline (no network, no API keys). Each service exposes a
backend interface with a real macOS/offline implementation and a mock used for
headless tests and CI. Backends are selected via environment variables:

- JARVIS_AUDIO    : 'sounddevice' | 'mock'   (default: mock off-Mac)
- JARVIS_WAKEWORD : 'openwakeword' | 'mock'  (default: mock off-Mac)
- JARVIS_STT      : 'whisper' | 'mock'       (default: mock off-Mac)
- JARVIS_TTS      : 'macos' | 'mock'         (default: mock off-Mac)
"""

from .audio import AudioService
from .wakeword import WakeWordService
from .stt import STTService
from .tts import TTSService

__all__ = ["AudioService", "WakeWordService", "STTService", "TTSService"]

# JARVIS V2

An AI Operating System layer for macOS, inspired by Iron Man's JARVIS. It lives
on the desktop as a single orb: it listens, understands, acts, and responds.

This repository contains the **deterministic core (Phase 2)** and the **voice
foundation + orb (Phase 1)**, both implemented and tested. Phase 3 (screen
understanding) is scaffolded.

## Philosophy: deterministic before intelligent

If JARVIS already knows how to perform a task, it executes immediately with
**no LLM in the path**. Reasoning is expensive and latency destroys the magic.
Intelligence is reserved for tasks deterministic systems cannot solve (Phase 3).

## Offline & security

Everything runs **fully offline** with no API keys and no telemetry:

- **Wake word:** openWakeWord (local ONNX 'hey jarvis' model)
- **STT:** faster-whisper (local, `base.en` by default; set `JARVIS_WHISPER_MODEL`)
- **TTS:** macOS built-in `say` binary
- **Orb:** PySide6

Security posture: pinned dependencies; no network calls; transcribed text is
treated as data and never executed; `say` is invoked with an argument list
(never a shell string) so transcripts can't cause command injection.

## Architecture

Service-oriented; each service has one responsibility and communicates through
an `EventBus`. The interaction loop:

```
idle -> wakeword.detected -> listening -> stt.transcript -> ActionEngine
     -> action.success/error -> tts.speak -> idle
```

```
JarvisApplication
  EventBus          core/events.py        pub/sub, error-isolated
  LifecycleManager  core/lifecycle.py     ordered start/stop
  Profiler          core/profiler.py      latency budgets
  Orchestrator      core/orchestrator.py  the interaction loop
  ActionRegistry    intent/registry.py    Action defs + alias index
  IntentMatcher     intent/matcher.py     deterministic phrase -> Action
  ActionEngine      actions/engine.py     resolve + execute via Backend
  AudioService      voice/audio.py        mic frames (sounddevice | mock)
  WakeWordService   voice/wakeword.py     openwakeword | mock
  STTService        voice/stt.py          whisper | mock
  TTSService        voice/tts.py          macOS say | mock
  OrbController     ui/states.py          event-driven state machine
  Orb widget        ui/orb.py             PySide6 frameless orb
```

Every backend has a real (macOS/offline) implementation and a `mock` used for
headless tests/CI, selected via env vars: `JARVIS_BACKEND`, `JARVIS_AUDIO`,
`JARVIS_WAKEWORD`, `JARVIS_STT`, `JARVIS_TTS` (each `...|mock`).

## Performance targets

| Stage              | Budget   |
|--------------------|----------|
| Wake detection     | < 100 ms |
| STT                | < 300 ms |
| Intent resolution  | < 50 ms  |
| Action execution   | < 100 ms |
| Orb animation      | 60 FPS   |

The `Profiler` logs a warning whenever a budget is exceeded.

## Running on macOS

```bash
pip install -r requirements.txt
python -m jarvis.main --gui   # orb + live voice
```

Grant **Microphone** and **Accessibility** permissions to your terminal in
System Settings > Privacy & Security. First run downloads the Whisper model
locally (one time), after which everything is offline.

### Manual verification checklist (real voice/orb)

CI cannot test real audio or the visible orb (headless Linux, no mic/display).
Verify these on your Mac:

1. Orb appears, is draggable, stays on top, transparent background.
2. Say "Jarvis" -> orb turns blue (listening).
3. "open chrome" / "paste" / "switch tab" / "press enter" execute.
4. "type hello world" types the text.
5. Unknown command -> spoken fallback, orb returns to idle.

## Headless REPL (no mic/GUI)

```bash
JARVIS_BACKEND=mock python -m jarvis.main   # type commands directly
```

## Tests

```bash
JARVIS_BACKEND=mock python -m pytest -q
```

CI runs the suite on Linux with all backends set to mock (see
`.gitlab-ci.yml`). This proves the wiring/state-machine/pipeline logic; real
voice and the visible orb are verified manually on macOS.

## Status

- **Phase 2 - Computer control:** implemented + tested.
- **Phase 1 - Voice + orb:** implemented + tested (pipeline via mocks; real
  audio/orb verified manually on macOS).
- **Phase 3 - Screen understanding:** scaffolded with interfaces and TODOs.

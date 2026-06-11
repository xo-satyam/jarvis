# JARVIS V2

An AI Operating System layer for macOS, inspired by Iron Man's JARVIS. It lives
on the desktop as a single orb: it listens, understands, acts, and responds.

This repository currently contains the **deterministic core (Phase 2)**, fully
implemented and tested, plus scaffolding for Phase 1 (voice) and Phase 3
(screen understanding).

## Philosophy: deterministic before intelligent

If JARVIS already knows how to perform a task, it executes immediately with
**no LLM in the path**. Reasoning is expensive and latency destroys the magic.
Actions like copy, paste, open Chrome, switch tab, type text, press enter and
scroll are predefined blocks of code resolved by alias matching. Intelligence
is reserved for tasks deterministic systems cannot solve (e.g. "explain this
error"), which belong to Phase 3.

## Architecture

Service-oriented. Each service has one responsibility and communicates through
an `EventBus`; services are never tightly coupled.

```
JarvisApplication
  EventBus            core/events.py      pub/sub, error-isolated
  LifecycleManager    core/lifecycle.py   ordered start/stop
  Profiler            core/profiler.py    latency budgets
  ActionRegistry      intent/registry.py  Action definitions + alias index
  IntentMatcher       intent/matcher.py   deterministic phrase -> Action
  ActionEngine        actions/engine.py   resolve + execute via Backend
  Backend             actions/backend.py  macOS (pyautogui/osascript) | mock
```

The `Backend` abstraction lets the engine run headless: tests and CI use a
`MockBackend` that records calls; macOS uses a real backend. Select with the
`JARVIS_BACKEND` env var (`mock` or `macos`).

## Performance targets

| Stage              | Budget   |
|--------------------|----------|
| Intent resolution  | < 50 ms  |
| Action execution   | < 100 ms |
| Wake detection     | < 100 ms (Phase 1) |
| STT                | < 300 ms (Phase 1) |
| Vision response    | < 2 s (Phase 3) |

The `Profiler` logs a warning whenever a budget is exceeded.

## Running

```bash
pip install -r requirements.txt
JARVIS_BACKEND=mock python -m jarvis.main   # type commands, no GUI needed
```

On macOS, omit `JARVIS_BACKEND` (or set `macos`) to drive the real OS; grant
Accessibility permissions to your terminal.

## Tests

```bash
JARVIS_BACKEND=mock python -m pytest -q
```

CI runs the suite on Linux with the mock backend (see `.gitlab-ci.yml`).

## Status

- **Phase 2 - Computer control:** implemented and tested.
- **Phase 1 - Voice (wake word, STT, TTS, orb):** scaffolded with interfaces
  and TODOs.
- **Phase 3 - Screen understanding (capture, OCR, analyze, explain):**
  scaffolded with interfaces and TODOs.

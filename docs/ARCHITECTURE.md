# AirBluez — Architecture

## Overview

AirBluez is a real-time, gesture-driven chord player. A webcam feed is
analyzed by MediaPipe's `HandLandmarker` (Tasks API). Hand landmarks are
converted into normalized features, classified into discrete gestures, and
combined with continuous spatial signals (angles, swipes) to drive a central
application state. The state is consumed by an audio engine and a pygame UI.

## High-Level Diagram

```text
┌─────────────┐   frames    ┌──────────────┐   landmarks   ┌──────────────┐
│   Webcam    │ ──────────► │ HandLandmarker│ ────────────► │  Feature     │
│  (OpenCV)   │             │  (MP Tasks)   │               │  Extractor   │
└─────────────┘             └──────────────┘               └──────┬───────┘
                                                                  │
                                  ┌───────────────────────────────┼───────────────────────┐
                                  ▼                               ▼                       ▼
                        ┌──────────────────┐           ┌────────────────────┐   ┌──────────────────┐
                        │ Gesture Classifier│          │  Wheel Mapper      │   │ Right-Hand       │
                        │ (MLP / RF + smooth)│         │ (angle → root)     │   │ Swipe Detector   │
                        └─────────┬────────┘           └─────────┬──────────┘   └────────┬─────────┘
                                  │                              │                       │
                                  └──────────────┬───────────────┴───────────────────────┘
                                                 ▼
                                       ┌────────────────────┐
                                       │  Reducer (pure)    │
                                       │   updates AppState │
                                       └─────────┬──────────┘
                                                 ▼
                                  ┌──────────────────────────────┐
                                  │ AppState (pydantic, single   │
                                  │ source of truth)             │
                                  └──────────┬───────────────────┘
                                             │
                              ┌──────────────┴───────────────┐
                              ▼                              ▼
                     ┌────────────────┐            ┌─────────────────┐
                     │ Audio Engine   │            │ UI Layer        │
                     │ (Pyo)          │            │ (pygame)        │
                     └────────────────┘            └─────────────────┘
```

## Modules

### `perception/`
Captures frames and produces structured `HandFrame` objects.

- `camera.py` — OpenCV capture; mirrors the frame before inference.
- `landmarker.py` — Wraps `mediapipe.tasks.python.vision.HandLandmarker` in
  `LIVE_STREAM` mode with an async result callback.
- `features.py` — Translation/scale-invariant feature vector from 21 landmarks.
- `schemas.py` — `HandFrame`, `Handedness`, and related dataclasses.

### `ml/`
Offline training and online inference for gesture classification.

- `collect_dataset.py` — Hotkey-driven labeling tool that writes CSVs.
- `train.py` — Trains MLP and Random Forest, persists best model with `joblib`.
- `classifier.py` — Inference wrapper with majority-vote temporal smoothing.
- `models/` — Saved `.joblib` artifacts.

### `controls/`
Translates perception output into discrete control intents.

- `wheel_mapper.py` — Maps left-hand angle to a chord root with hysteresis.
- `right_hand.py` — Detects horizontal/vertical swipes for sample and volume.

### `state/`
Single source of truth.

- `app_state.py` — Pydantic model: `play, chord_root, chord_quality,
  sample_id, volume`.
- `reducer.py` — Pure functions producing the next state from intents.

### `audio/`
Real-time audio synthesis and sample playback.

- `engine.py` — Pyo server lifecycle.
- `theory.py` — Chord interval tables.
- `chord_player.py` — Builds voicings, crossfades transitions.
- `sample_bank.py` — Instrument preset switching.

### `ui/`
Pygame rendering at 60 FPS.

- `app.py` — Main loop, subscribes to state changes.
- `wheel.py` — Camelot-style chord wheel renderer.
- `hud.py` — Top bar with chord, sample, volume, play state.
- `overlay.py` — Debug landmark overlay.

## Data Flow

1. **Capture (Thread A):** OpenCV reads a frame, mirrors it, converts to RGB,
   wraps in `mp.Image`, and calls `landmarker.detect_async(image, timestamp_ms)`.
2. **Landmark callback:** MediaPipe returns landmarks + handedness; the wrapper
   builds a `HandFrame` and pushes it onto a bounded `Queue(maxsize=2)`.
3. **Main thread (Thread B):** Drains the queue, computes features, runs the
   gesture classifier, derives wheel angle and right-hand swipes.
4. **Reduce:** Intents are dispatched to `state.reducer`, producing the next
   `AppState`.
5. **Audio + UI:** Both subscribe to state-change events. Audio crossfades to
   the new chord; UI redraws wheel and HUD.

## Threading Model

- **Thread A — Perception:** capture + landmarker callback. Drops stale frames
  to keep latency bounded.
- **Thread B — Main:** classification, reducing, and UI rendering.
- **Audio Thread:** managed internally by Pyo.

Inter-thread communication uses a single `Queue(maxsize=2)`. The reducer is
pure and called only from the main thread.

## Latency Budget

Target end-to-end latency (gesture → sound) **< 100 ms**:

| Stage              | Budget   |
|--------------------|----------|
| Capture + mirror   | ~10 ms   |
| HandLandmarker     | ~25 ms   |
| Features + classify| ~5 ms    |
| Reducer + dispatch | ~1 ms    |
| Audio crossfade    | 50–80 ms |

## Key Design Decisions

- **MediaPipe Tasks API over legacy `mp.solutions.hands`** — actively
  maintained; supports async `LIVE_STREAM`; cleaner config.
- **Classify on landmarks, not pixels** — MLP/RF over normalized features is
  faster, smaller, and more interpretable than a CNN.
- **Pure reducer + Pydantic state** — testable, predictable, decoupled from
  audio and UI.
- **Hysteresis and smoothing everywhere continuous becomes discrete** —
  prevents jitter on chord boundaries and gesture flicker.
- **Crossfaded audio transitions** — eliminates clicks on chord/sample changes.

## Testing Strategy

- **Unit:** features (invariants), wheel mapper (boundaries/hysteresis),
  reducer (state transitions), theory (interval correctness).
- **Integration:** synthetic landmark sequences fed through the full pipeline.
- **Manual:** record short webcam clips per milestone for regression checks.

## Extensibility

- **Arpeggiator mode** — replace `chord_player` voicing with timed note
  sequencer.
- **MIDI / OSC output** — add an `io/` module that subscribes to state.
- **Custom wheel layouts** — `wheel_mapper` already takes a configurable root
  ordering (chromatic, Camelot, circle of fifths).

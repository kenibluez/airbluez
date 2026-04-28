# AirBluez — Gesture Vocabulary

This document defines every gesture the application recognizes, how it is
detected, and what application state it produces.

## Hand Roles

| Hand   | Responsibility                                                     |
|--------|--------------------------------------------------------------------|
| Left   | Selects chord root (via wrist angle) and chord quality (via shape) |
| Right  | Modifies environment: sample selection and volume                  |

> **Mirror note:** the camera feed is mirrored before inference, so MediaPipe's
> reported handedness matches the user's perspective ("left" = user's left hand).

---

## Left Hand — Chord Selection

### Root Selection (continuous)

The chord root is determined by the **angle of the vector from wrist to index
finger MCP** relative to the screen center. The angle is mapped to 12 segments
arranged on a wheel:

```text
C, D, E, F, G, A, B, C♭, D♭, F♭, G♭, A♭,
```

- **Hysteresis:** the active root only changes when the angle crosses the
  next segment boundary by **more than 5°**, preventing flicker at edges.
- The active segment is highlighted in the UI wheel.

### Quality Selection (discrete gesture classes)

| Gesture     | Hand shape                              | Chord quality | Label       |
|-------------|------------------------------------------|---------------|-------------|
| Closed fist | All fingers curled                       | (paused)      | `closed`    |
| Open hand   | All five fingers extended                | major (play)  | `open`      |
| One finger  | Index extended only                      | augmented     | `one`       |
| Two fingers | Index + middle extended                  | diminished    | `two`       |
| Three fingers | Index + middle + ring extended         | minor         | `three`     |
| Four fingers | Index + middle + ring + pinky extended  | maj7          | `four`      |
| Pinch       | Thumb tip touching index tip             | suspended     | `pinch`     |

### Play / Pause

- **`closed`** → `play = False` (audio fades out).
- Any other valid gesture → `play = True` (audio fades in with the new chord).

### Detection Notes

- Finger-extended booleans are computed from joint angles and tip-vs-MCP
  distances (scale-invariant).
- The `pinch` class is determined by the normalized distance between thumb tip
  (landmark 4) and index tip (landmark 8) being below a threshold.
- Predictions are smoothed with a **majority vote over the last 5 frames** to
  suppress jitter.

---

## Right Hand — Environmental Modifiers

Right-hand gestures are pose classes used to **arm** a continuous control. The
actual change is driven by fingertip motion within a rolling 0.5 s window.

### Pose Classes

| Pose         | Description                              | Armed control     |
|--------------|------------------------------------------|-------------------|
| `index_up`   | Index extended, pointing upward          | Sample navigation |
| `index_left` | Index extended, pointing left (sideways) | Volume control    |
| `other`      | Anything else                            | No-op             |

### Sample Navigation (`index_up`)

- Track horizontal displacement of the index fingertip (landmark 8) over the
  last 0.5 s.
- When `|Δx|` exceeds the swipe threshold:
  - **Right swipe** → `sample_id += 1`
  - **Left swipe** → `sample_id -= 1`
- `sample_id` wraps within the loaded sample bank.
- A **300 ms debounce** prevents repeated triggers from a single gesture.

### Volume Control (`index_left`)

- Track vertical displacement of the index fingertip over the last 0.5 s.
- `volume += k * Δy`, clamped to `[0.0, 1.0]`.
- Updates apply continuously while the pose is held — no debounce.
- Audio engine smooths gain changes with a **50 ms ramp** to avoid zipper noise.

---

## Gesture Lifecycle

1. **Detect** — landmarker emits 21 landmarks per hand at ~30 FPS.
2. **Featurize** — normalize (translate to wrist, scale by middle MCP distance).
3. **Classify** — MLP (or RF fallback) predicts the discrete class.
4. **Smooth** — majority vote over a 5-frame ring buffer.
5. **Map** — combine with continuous signals (wheel angle, swipe deltas).
6. **Reduce** — produce next `AppState` via pure reducer.
7. **Render & sound** — UI and audio engine react to state change.

---

## Calibration & Best Practices

- **Lighting:** train and use under similar lighting conditions; collect data
  in multiple environments for robustness.
- **Distance:** keep hands roughly 30–80 cm from the camera.
- **Framing:** avoid hands leaving the frame edges, where landmark accuracy
  degrades.
- **Background:** plain backgrounds improve detection confidence.
- **Thumb visibility:** the `two` vs `three` classifier relies on thumb state;
  keep the thumb clearly tucked or extended, not partially raised.

---

## Adding a New Gesture

1. Define the class label in `airbluez/ml/collect_dataset.py`.
2. Collect ~300 samples across different lighting and users.
3. Retrain via `python -m airbluez.ml.train`.
4. Map the new label to an action in `state/reducer.py`.
5. Document it in this file under the appropriate hand section.
6. Add a unit test exercising the new transition in `tests/test_reducer.py`.

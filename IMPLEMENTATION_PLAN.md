# AirBluez — Full Implementation Plan

A complete, opinionated build guide: architecture, milestones, conventions, and concrete steps using the modern **MediaPipe Tasks API** (`mediapipe.tasks.python.vision.HandLandmarker`).

---

## 1. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Hand tracking | `mediapipe` Tasks API (`HandLandmarker`) | Modern API, replaces legacy `mp.solutions.hands` |
| Model bundle | `hand_landmarker.task` | Downloaded from Google's MediaPipe model zoo |
| ML | `scikit-learn` (MLP + RF) | Train on landmark features |
| Audio | `pyo` (preferred) or `pygame.mixer` | Real-time synthesis & sample playback |
| UI | `pygame` | Lightweight, 60 FPS |
| Lang/Tooling | Python 3.11+, `ruff`, `black`, `mypy`, `pytest`, `pre-commit` |

---

## 2. Folder Architecture

```text
airbluez/
├── airbluez/                        # Source package
│   ├── __init__.py
│   ├── main.py                      # Entry point
│   ├── config.py                    # Constants, paths, thresholds
│   │
│   ├── perception/
│   │   ├── __init__.py
│   │   ├── camera.py                # OpenCV capture wrapper
│   │   ├── landmarker.py            # MediaPipe Tasks HandLandmarker wrapper
│   │   ├── features.py              # Landmark → feature vector
│   │   └── schemas.py               # HandFrame, Handedness dataclasses
│   │
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── collect_dataset.py       # Data-collection CLI
│   │   ├── train.py                 # Train MLP/RF, save with joblib
│   │   ├── classifier.py            # Inference wrapper + smoothing
│   │   └── models/                  # Saved .joblib models
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── app_state.py             # Pydantic AppState
│   │   └── reducer.py               # Pure state transitions
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── engine.py                # Pyo server lifecycle
│   │   ├── chord_player.py          # Root + quality → voicing
│   │   ├── sample_bank.py           # Instrument/preset switching
│   │   └── theory.py                # Chord intervals, note maps
│   │
│   ├── controls/
│   │   ├── __init__.py
│   │   ├── wheel_mapper.py          # Angle → chord root (with hysteresis)
│   │   └── right_hand.py            # Swipe/slide detection (sample, volume)
│   │
│   └── ui/
│       ├── __init__.py
│       ├── app.py                   # Pygame loop
│       ├── wheel.py                 # Camelot-style wheel renderer
│       ├── hud.py                   # Top/bottom info bar
│       └── overlay.py               # Hand skeleton debug overlay
│
├── assets/
│   ├── models/
│   │   └── hand_landmarker.task     # Downloaded MP model
│   ├── samples/                     # WAVs per instrument
│   └── fonts/
│
├── data/
│   └── gestures/                    # CSVs from data collection
│
├── scripts/
│   ├── download_models.sh           # Fetch hand_landmarker.task
│   └── run.sh
│
├── tests/
│   ├── test_features.py
│   ├── test_wheel_mapper.py
│   ├── test_reducer.py
│   └── test_theory.py
│
├── docs/
│   ├── architecture.md
│   └── gestures.md
│
├── .pre-commit-config.yaml
├── .gitignore
├── pyproject.toml                   # ruff, black, mypy, deps
├── README.md
└── LICENSE
```

---

## 3. Conventions

### 3.1 Code Style
- **PEP 8** enforced via **ruff** + **black** (line length 100).
- Type hints required on all public functions; checked with **mypy --strict** for `airbluez/`.
- Docstrings: **Google style**.
- Imports sorted by **ruff (isort rules)**.
- No magic numbers — put thresholds in `config.py`.

### 3.2 Naming
- Modules/files: `snake_case.py`
- Classes: `PascalCase`
- Funcs/vars: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix `_`

### 3.3 Git / Commits — Conventional Commits
Format: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `build`, `ci`, `style`.

Examples:
```text
feat(perception): add HandLandmarker wrapper using Tasks API
feat(ml): train MLP gesture classifier with 7 classes
fix(audio): prevent click on chord crossfade
refactor(state): extract reducer into pure module
docs(readme): document gesture vocabulary
test(controls): cover wheel hysteresis edge cases
```

### 3.4 Branching
- `main` — always shippable.
- `dev` — integration.
- Feature branches: `feat/<scope>-<short-desc>`, e.g. `feat/perception-landmarker`.
- PRs squash-merged with a Conventional Commit title.

### 3.5 Tooling
- `pre-commit` runs ruff, black, mypy, and pytest-fast on staged files.
- Tag releases with **SemVer**: `v0.1.0`, `v0.2.0`...
- `CHANGELOG.md` auto-generated from commits (e.g. `git-cliff`).

### 3.6 Project-Specific Rules
- Perception layer **never** touches audio or UI — only emits `HandFrame`.
- All state mutations go through `state.reducer` (pure functions, easy to test).
- Audio crossfades minimum **50 ms** to prevent clicks.
- Frame loop must drop stale frames (`queue.Queue(maxsize=2)`).

---

## 4. MediaPipe Tasks API Setup

Use the **modern** API, not `mp.solutions.hands`.

```bash
mkdir -p assets/models
curl -L -o assets/models/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

```python
# airbluez/perception/landmarker.py
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import mediapipe as mp

def build_landmarker(model_path: str) -> vision.HandLandmarker:
    base_options = mp_python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        result_callback=_on_result,  # async callback in LIVE_STREAM mode
    )
    return vision.HandLandmarker.create_from_options(options)
```

Key differences from legacy API:
- Async **`LIVE_STREAM`** mode with `result_callback`.
- Frames passed as `mp.Image` (`mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_array)`).
- Call `landmarker.detect_async(mp_image, timestamp_ms)` per frame.
- Result includes `hand_landmarks`, `hand_world_landmarks`, `handedness`.

---

## 5. Development Phases & Milestones

### Phase 0 — Bootstrap (½ day)

**Goal:** Repo, tooling, CI green.

1. `git init`, add `.gitignore`, license, README skeleton.
2. Create `pyproject.toml` with ruff/black/mypy config.
3. Install pre-commit hooks.
4. Set up GitHub Actions: lint + test on push.
5. Run `scripts/download_models.sh` to fetch `hand_landmarker.task`.

Commits:
- `chore(repo): initialize project structure`
- `build(deps): add mediapipe, scikit-learn, pyo, pygame`
- `ci: add lint and test workflow`

---

### Phase 1 — Perception Spike (M1, ~1 day)

**Goal:** Render webcam with hand landmarks via Tasks API.

1. Implement `perception/camera.py` (OpenCV capture, mirror flip).
2. Implement `perception/landmarker.py` using `HandLandmarker` in `LIVE_STREAM` mode.
3. Define `schemas.py`: `HandFrame { handedness, landmarks_xy, landmarks_world, timestamp }`.
4. Build a tiny `scripts/debug_landmarks.py` that draws landmarks via OpenCV.
5. Verify ~30 FPS, correct handedness post-mirror.

Commits:
- `feat(perception): wrap HandLandmarker Tasks API`
- `feat(perception): add camera capture with mirror handling`
- `docs(perception): explain handedness inversion after mirror`

---

### Phase 2 — Feature Extraction + Dataset (M2a, ~1 day)

**Goal:** Reproducible feature vectors and a labeled dataset.

1. Implement `perception/features.py`:
   - Translate landmarks so wrist = origin.
   - Scale by middle-finger MCP distance.
   - Compute: 5 finger-extended booleans, fingertip pairwise distances, palm-normal angle, wrist→index angle.
2. Implement `ml/collect_dataset.py`:
   - Live preview, hotkeys 0–9 to label, write rows to `data/gestures/<hand>.csv`.
   - Classes: left = `{closed, open, one, two, three, four, pinch}`; right = `{index_up, index_left, other}`.
3. Collect ~300 samples/class in varied lighting.

Commits:
- `feat(perception): add normalized landmark feature extractor`
- `feat(ml): add gesture data collection CLI`
- `docs(gestures): document gesture vocabulary`

---

### Phase 3 — Train Classifier (M2b, ~1 day)

**Goal:** Robust gesture classifier with smoothing.

1. `ml/train.py`: train MLP (`(64,32)`) and RF; pick higher F1 on stratified split. Save `.joblib`.
2. `ml/classifier.py`: load model, expose `predict(features) → label`, with **majority-vote smoothing** over last 5 frames.
3. Add `tests/test_features.py` with synthetic landmarks for invariants.

Acceptance: ≥95% val accuracy per hand.

Commits:
- `feat(ml): train MLP and RF gesture classifiers`
- `feat(ml): add temporal smoothing to inference`
- `test(ml): cover feature normalization invariants`

---

### Phase 4 — Wheel Mapping (M3, ½ day)

**Goal:** Left-hand angle drives chord root selection.

1. `controls/wheel_mapper.py`:
   - Compute angle of `wrist → index_MCP` vs screen center.
   - Map to 12 roots in Camelot order (configurable).
   - **Hysteresis**: switch only when crossing next slot by >5°.
2. Print `chord_root + chord_quality` (from gesture) to console.
3. `tests/test_wheel_mapper.py` for edge angles & hysteresis.

Commits:
- `feat(controls): map left-hand angle to chord root with hysteresis`
- `test(controls): cover wheel boundary cases`

---

### Phase 5 — Audio Engine (M4, ~1–2 days)

**Goal:** Correct chord plays on demand with smooth transitions.

1. `audio/theory.py`: chord interval tables (`maj7`, `min`, `dim`, `aug`, `sus`).
2. `audio/engine.py`: start/stop Pyo server.
3. `audio/chord_player.py`: build voicing from `(root, quality)`, output via Pyo synth voice; 50–80 ms crossfade between chords; fade-out on `play=False`.
4. `audio/sample_bank.py`: load presets/samples (Rhodes, pad, piano, guitar).
5. Hook console-driven tests for chord switching.

Commits:
- `feat(audio): add chord theory tables and voicing builder`
- `feat(audio): integrate pyo engine with crossfaded chord playback`
- `feat(audio): add sample bank with preset switching`
- `fix(audio): ramp gain to remove transition clicks`

---

### Phase 6 — Right Hand Controls (M5, ~1 day)

**Goal:** Sample navigation and volume control via swipes.

1. `controls/right_hand.py`:
   - On `index_up`: track horizontal fingertip delta in a 0.5 s window; threshold + 300 ms debounce → `sample_index ± 1`.
   - On `index_left`: vertical delta → `volume += k*delta`, clamped [0,1].
2. Wire into `state/reducer.py`.
3. Tests for debounce and clamping.

Commits:
- `feat(controls): detect right-hand swipes for sample and volume`
- `test(controls): debounce and clamping edge cases`

---

### Phase 7 — State Machine Integration (~½ day)

**Goal:** Single source of truth.

1. `state/app_state.py` (Pydantic):
   ```text
   play: bool, chord_root: str, chord_quality: str,
   sample_id: int, volume: float
   ```
2. `state/reducer.py`: pure functions `apply_left_hand`, `apply_right_hand`, `apply_play_pause`.
3. Audio + UI subscribe to state changes (simple observer / callback list).

Commits:
- `feat(state): add pydantic AppState and pure reducer`
- `refactor: route all mutations through reducer`

---

### Phase 8 — UI Layer (M6, ~1–2 days)

**Goal:** Polished pygame UI.

1. `ui/wheel.py`: 12-segment wheel, highlight active root, indicator for hand angle.
2. `ui/hud.py`: top bar `Chord: Cmaj7 | Sample: Rhodes | Vol: 72% | ▶`.
3. `ui/overlay.py`: optional hand skeleton (debug toggle).
4. `ui/app.py`: 60 FPS loop, consumes state, renders.

Commits:
- `feat(ui): render Camelot-style chord wheel`
- `feat(ui): add HUD with chord, sample, volume`
- `feat(ui): add debug landmark overlay`

---

### Phase 9 — Threading & Performance (~½ day)

**Goal:** <100 ms gesture→sound latency.

1. Thread A: capture + landmarker + classifier → `Queue(maxsize=2)`.
2. Thread B (main): drain queue → reducer → UI render.
3. Pyo runs its own audio thread.
4. Profile with `cProfile`; ensure no thread blocks >10 ms.

Commits:
- `perf(app): decouple perception thread from render loop`
- `perf(perception): drop stale frames to bound latency`

---

### Phase 10 — Polish & Stretch (M7–M8)

- Expand dataset for robustness (different users/lighting).
- Add visual feedback for swipes (animated arrow).
- **Stretch:** arpeggiator mode, loop recorder, MIDI export, OSC out for DAW integration.
- Write `docs/architecture.md` + GIF demo.

Commits:
- `feat(audio): add arpeggiator mode`
- `feat(io): export MIDI from played chord sequence`
- `docs: add architecture diagram and demo gif`

---

## 6. Definition of Done (per milestone)

A milestone is "done" only if:
- ✅ Lint, type-check, tests pass in CI.
- ✅ Feature documented in `docs/` or README.
- ✅ Manually verified on webcam (record short clip).
- ✅ Tagged commit on `dev` and merged via PR.

---

## 7. Pitfalls Recap

- **Don't** use `mp.solutions.hands` — use Tasks API (`HandLandmarker`).
- **Mirror** the frame *before* feeding MediaPipe, then trust handedness.
- Always provide **monotonic timestamps** (ms) to `detect_async`.
- Add **hysteresis + smoothing** everywhere continuous → discrete.
- **Crossfade** every audio transition.

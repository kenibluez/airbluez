# AirBluez

AirBluez is a real-time, gesture-driven virtual instrument that transforms your hand movements into musical chords. Using computer vision and machine learning, it tracks your hands through a webcam to map spatial positions and gestures to musical intent.

## 🚀 Features

- **Gesture-Controlled Chords**: Select chord roots by moving your left hand in a circular "chord wheel" and choose chord qualities (Major, Minor, etc.) with hand gestures.
- **Instrument Bank**: Switch between different synthesizer presets (Square, Synth, Pad, Saw) using right-hand swipes.
- **Dynamic Volume**: Control output volume with vertical right-hand movements.
- **Real-Time Visualization**: Interactive Pygame HUD featuring a chord wheel, hand landmark overlays, and status indicators.
- **Low Latency**: Optimized pipeline using MediaPipe Tasks API and the Pyo audio engine for responsive performance.

## 🛠 Tech Stack

- **Perception**: [MediaPipe](https://mediapipe.dev/) Tasks API (Hand Landmarker)
- **Machine Learning**: [scikit-learn](https://scikit-learn.org/) (MLP/Random Forest)
- **Audio Engine**: [Pyo](https://ajaxsoundstudio.com/software/pyo/)
- **UI/Graphics**: [Pygame](https://www.pygame.org/)
- **Language**: Python 3.11+

## 📦 Installation

### 1. Prerequisites
Ensure you have Python 3.11+ installed. You may also need to install portaudio and libsndfile for the `pyo` audio engine:
```bash
# Ubuntu/Debian
sudo apt-get install libportaudio2 libsndfile1-dev
```

### 2. Clone and Setup
```bash
git clone https://github.com/yourusername/airbluez.git
cd airbluez
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Download Models
Download the MediaPipe hand landmarker model:
```bash
bash scripts/download_models.sh
```

## 🎮 Usage

### Running the App
```bash
python -m airbluez.main
```

### Controls
- **Left Hand**:
    - **Position**: Move around the center of the screen to select the **Chord Root** (C, D, E, etc.).
    - **Gesture**: Hand shape determines the **Chord Quality**, see [docs/GESTURES.md](docs/GESTURES.md) for the specifics.
- **Right Hand**:
    - **Horizontal Swipe**: Cycle through available **Instruments**.
    - **Vertical Slide**: Adjust **Volume**.

## 🏗 Architecture

AirBluez follows a decoupled architecture with a central state machine:
1. **Perception Layer**: Captures webcam frames and extracts 21 hand landmarks.
2. **Control Logic**: Maps landmarks to musical intents (Wheel mapping, Gesture classification).
3. **State Reducer**: Updates a central `AppState` (Pydantic model) based on intents.
4. **Output Layers**: Audio (Pyo) and UI (Pygame) react to state changes independently.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for more details.

## 🧪 Development

### Data Collection & Training
To train the gesture classifier on your own hands:
1. Run `python -m airbluez.ml.collect_dataset` to record landmark data.
2. Run `python -m airbluez.ml.train` to train the models.

### Testing
```bash
pytest
```

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

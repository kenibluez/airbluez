import queue
import sys
import threading
import time

import cv2
import mediapipe as mp
import numpy as np
import pygame

from airbluez.audio.chord_player import ChordPlayer

# Audio
from airbluez.audio.engine import AudioEngine
from airbluez.audio.sample_bank import SampleBank
from airbluez.controls.right_hand import RightHandController
from airbluez.controls.wheel_mapper import WheelMapper
from airbluez.ml.classifier import GestureClassifier

# Perception & ML
from airbluez.perception.camera import Camera
from airbluez.perception.features import extract_features
from airbluez.perception.landmarker import build_landmarker
from airbluez.perception.schemas import HandFrame

# State & Controls
from airbluez.state.app_state import AppState
from airbluez.state.reducer import apply_left_hand, apply_play_pause, apply_right_hand
from airbluez.state.store import Store

# UI
from airbluez.ui.hud import HUD
from airbluez.ui.overlay import DebugOverlay
from airbluez.ui.wheel import ChordWheel

# maxsize=2 ensures we drop stale frames to bound latency
event_queue = queue.Queue(maxsize=2)


def main():
    print("Initializing AirBluez...")

    # 1. Initialize State Store
    store = Store(AppState())

    # 2. Initialize Audio Engine
    audio_engine = AudioEngine()
    audio_engine.start()
    sample_bank = SampleBank()
    player = ChordPlayer(sample_bank, crossfade_ms=50)

    def _on_state_change(old_state: AppState, new_state: AppState):
        # Sync sample bank index
        sample_bank.current_idx = new_state.sample_id

        if not new_state.play:
            player.stop()
        else:
            player.play(new_state.chord_root, new_state.chord_quality, new_state.volume)

    store.subscribe(_on_state_change)

    # 3. Initialize ML & Controls
    left_clf = GestureClassifier("left", window_size=5)
    right_clf = GestureClassifier("right", window_size=5)
    wheel_mapper = WheelMapper(hysteresis_deg=5.0)
    right_controller = RightHandController(debounce_sec=0.4)

    # 4. MediaPipe Callback
    def _on_result(result, output_image: mp.Image, timestamp_ms: int):
        left_hand, right_hand = None, None

        if result.hand_landmarks:
            for idx, hlm in enumerate(result.hand_landmarks):
                raw_label = result.handedness[idx][0].category_name
                label = "Left" if raw_label == "Right" else "Right"

                world_coords = [(lm.x, lm.y, lm.z) for lm in result.hand_world_landmarks[idx]]
                xy_coords = [(lm.x, lm.y) for lm in hlm]

                frame = HandFrame(label, xy_coords, world_coords, timestamp_ms)
                if label == "Left":
                    left_hand = frame
                else:
                    right_hand = frame

        parsed_data = {
            "left_hand": left_hand,
            "right_hand": right_hand,
            "left_gesture": None,
            "right_gesture": None,
            "image": output_image.numpy_view(),  # <--- Grab the raw RGB frame here!
        }

        if left_hand:
            feats = extract_features(left_hand)
            parsed_data["left_gesture"] = left_clf.predict(feats)

        if right_hand:
            feats = extract_features(right_hand)
            parsed_data["right_gesture"] = right_clf.predict(feats)

        try:
            event_queue.put_nowait(parsed_data)
        except queue.Full:
            pass

    # 5. Initialize Camera
    cam = Camera(0)
    landmarker = build_landmarker("assets/models/hand_landmarker.task", _on_result)

    # 6. Camera Thread
    running = True

    def camera_worker():
        with landmarker:
            while running:
                ret, frame = cam.read_frame()
                if not ret:
                    continue
                # Resize frame to match Pygame window if necessary, assuming 800x600 for now
                frame = cv2.resize(frame, (800, 600))
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                landmarker.detect_async(mp_image, int(time.monotonic() * 1000))

    cam_thread = threading.Thread(target=camera_worker, daemon=True)
    cam_thread.start()

    # 7. Initialize UI
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("AirBluez")
    clock = pygame.time.Clock()

    hud = HUD(800)
    # Move X from 400 (center) to 240 (left side)
    wheel = ChordWheel(center=(240, 300), radius=200)
    overlay = DebugOverlay()
    show_debug = True

    print("AirBluez Ready! Press SPACE to toggle Play/Pause. Press 'd' to toggle debug skeleton.")

    # Keep track of the last data frame for rendering if the queue is empty this tick
    last_data = None

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        new_state = apply_play_pause(store.state, not store.state.play)
                        store.dispatch(new_state)
                    elif event.key == pygame.K_d:
                        show_debug = not show_debug

            try:
                last_data = event_queue.get_nowait()
                state = store.state

                # Left Hand: Map Chord
                if last_data["left_hand"] and last_data["left_gesture"]:
                    # Use landmark 9 (Middle Finger MCP) as a stable tracking point for the palm center
                    hand_center = last_data["left_hand"].landmarks_xy[9]

                    # Move the math anchor X from 0.5 (50%) to 0.3 (30%)
                    # (240 pixels is exactly 30% of your 800 pixel width)
                    root = wheel_mapper.get_root_from_position(hand_center, anchor=(0.3, 0.5))

                    quality = last_data["left_gesture"]
                    if type(quality).__name__ == "ndarray" or isinstance(quality, list):
                        quality = quality[0]
                    quality = str(quality).lower().strip()

                    # 1. Closed means Pause
                    if quality == "closed":
                        state = apply_play_pause(state, False)
                    else:
                        # 2. Map the remaining gestures
                        theory_map = {
                            "open": "major",
                            "three": "minor",
                            "pinch": "aug",
                            "one": "dim",
                            "two": "aug",
                            "four": "maj7",
                        }
                        mapped_quality = theory_map.get(quality, "major")

                        state = apply_left_hand(state, root, mapped_quality)

                        if not state.play:
                            state = apply_play_pause(state, True)

                if last_data["right_hand"] and last_data["right_gesture"]:
                    tip_x = last_data["right_hand"].landmarks_xy[8][0]
                    tip_y = last_data["right_hand"].landmarks_xy[8][1]

                    sample_delta, new_vol = right_controller.process(
                        last_data["right_gesture"], tip_x, tip_y
                    )
                    state = apply_right_hand(state, sample_delta, new_vol, max_samples=4)

                store.dispatch(state)

            except queue.Empty:
                pass

            # RENDER PIPELINE
            if last_data is not None:
                # 1. Draw Camera Feed
                surf = pygame.surfarray.make_surface(last_data["image"].swapaxes(0, 1))
                screen.blit(surf, (0, 0))

                # 2. Draw Wheel (Transparent) and HUD
                wheel.draw(screen, store.state)
                hud.draw(screen, store.state)

                # 3. Draw Debug Skeleton ON TOP of the wheel
                if show_debug:
                    if last_data["left_hand"]:
                        overlay.draw_landmarks(screen, last_data["left_hand"], 800, 600)
                        overlay.draw_anchor_tether(
                            screen,
                            last_data["left_hand"],
                            wheel_center=(240, 300),  # This matches your wheel's UI center
                            width=800,
                            height=600,
                        )
                    if last_data["right_hand"]:
                        overlay.draw_landmarks(screen, last_data["right_hand"], 800, 600)

                    debug_font = pygame.font.SysFont("Arial", 24, bold=True)
                    l_text = f"L-AI: {last_data['left_gesture']}"
                    r_text = f"R-AI: {last_data['right_gesture']}"
                    screen.blit(debug_font.render(l_text, True, (0, 255, 0)), (20, 60))
                    screen.blit(debug_font.render(r_text, True, (0, 255, 255)), (20, 90))
            else:
                screen.fill((30, 30, 30))

            pygame.display.flip()
            clock.tick(60)

    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down...")
        running = False
        cam_thread.join(timeout=1.0)
        cam.release()
        audio_engine.stop()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()

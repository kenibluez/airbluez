import argparse
import csv
import os
import queue
import time

import cv2
import mediapipe as mp

from airbluez.perception.camera import Camera
from airbluez.perception.features import extract_features, get_feature_names
from airbluez.perception.landmarker import build_landmarker
from airbluez.perception.schemas import HandFrame

result_queue = queue.Queue(maxsize=2)


def _on_result(result, output_image: mp.Image, timestamp_ms: int):
    try:
        result_queue.put_nowait((result, output_image.numpy_view(), timestamp_ms))
    except queue.Full:
        pass


# Define the gesture vocabulary per hand
CLASSES_LEFT = {
    "0": "closed",
    "1": "open",
    "2": "one",
    "3": "two",
    "4": "three",
    "5": "four",
    "6": "pinch",
}
CLASSES_RIGHT = {"0": "index_up", "1": "index_left", "2": "other"}


def main():
    parser = argparse.ArgumentParser(description="Collect gesture dataset")
    parser.add_argument(
        "--hand", choices=["left", "right"], required=True, help="Which hand to collect data for"
    )
    args = parser.parse_args()

    target_hand = args.hand.capitalize()  # "Left" or "Right"
    class_map = CLASSES_LEFT if target_hand == "Left" else CLASSES_RIGHT

    csv_file = f"data/gestures/{args.hand}.csv"
    file_exists = os.path.isfile(csv_file)

    # Open CSV in append mode
    with open(csv_file, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["label"] + get_feature_names())

        cam = Camera(0)
        landmarker = build_landmarker("assets/models/hand_landmarker.task", _on_result)

        print(f"\n--- Collecting for {target_hand} Hand ---")
        print("Press these keys to capture a frame:")
        for key, label in class_map.items():
            print(f"  {key} -> {label}")
        print("Press 'q' to quit.\n")

        counts = {label: 0 for label in class_map.values()}

        with landmarker:
            while True:
                ret, frame = cam.read_frame()
                if not ret:
                    continue

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                landmarker.detect_async(mp_image, int(time.monotonic() * 1000))

                try:
                    result, result_frame, _ = result_queue.get(timeout=0.05)
                    annotated = cv2.cvtColor(result_frame, cv2.COLOR_RGB2BGR)

                    target_hand_frame = None

                    if result.hand_landmarks:
                        for idx, hlm in enumerate(result.hand_landmarks):
                            raw_label = result.handedness[idx][0].category_name
                            # Correct the mirror inversion
                            corrected_label = "Left" if raw_label == "Right" else "Right"

                            if corrected_label == target_hand:
                                # Extract coordinates for features
                                world_coords = [
                                    (lm.x, lm.y, lm.z) for lm in result.hand_world_landmarks[idx]
                                ]
                                target_hand_frame = HandFrame(
                                    handedness=corrected_label,
                                    landmarks_xy=[(lm.x, lm.y) for lm in hlm],
                                    landmarks_world=world_coords,
                                    timestamp_ms=0,  # Not needed for static extraction
                                )

                                # Draw green bounding box hint
                                h, w, _ = annotated.shape
                                px_x = [int(lm.x * w) for lm in hlm]
                                px_y = [int(lm.y * h) for lm in hlm]
                                cv2.rectangle(
                                    annotated,
                                    (min(px_x) - 20, min(px_y) - 20),
                                    (max(px_x) + 20, max(px_y) + 20),
                                    (0, 255, 0),
                                    2,
                                )

                    # Render UI text
                    y_offset = 30
                    cv2.putText(
                        annotated,
                        f"Target: {target_hand} Hand",
                        (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                    )
                    for label, count in counts.items():
                        y_offset += 25
                        cv2.putText(
                            annotated,
                            f"{label}: {count}",
                            (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 255),
                            1,
                        )

                    cv2.imshow("Dataset Collection", annotated)

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break

                    # If a valid hotkey is pressed and the target hand is visible
                    char_key = chr(key) if key < 256 else ""
                    if char_key in class_map and target_hand_frame:
                        label = class_map[char_key]
                        features = extract_features(target_hand_frame)
                        writer.writerow([label] + features)
                        counts[label] += 1
                        print(f"Saved: {label} (Total: {counts[label]})")

                except queue.Empty:
                    cv2.imshow("Dataset Collection", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

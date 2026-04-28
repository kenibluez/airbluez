import queue
import time

import cv2
import mediapipe as mp
import numpy as np

from airbluez.perception.camera import Camera
from airbluez.perception.landmarker import build_landmarker

# Thread-safe queue to pass results from MediaPipe's async callback to the main thread
result_queue = queue.Queue(maxsize=2)


def _on_result(result, output_image: mp.Image, timestamp_ms: int):
    try:
        # Push raw results to the queue for rendering
        result_queue.put_nowait((result, output_image.numpy_view(), timestamp_ms))
    except queue.Full:
        pass  # Drop stale frames to keep up with the live feed


# Define standard hand skeleton connections
HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),  # Thumb
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),  # Index
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),  # Middle
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),  # Ring
    (13, 17),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),  # Pinky & Palm base
]


def draw_landmarks(frame, hand_landmarks):
    """Draws a pure OpenCV skeleton over the landmarks."""
    h, w, _ = frame.shape

    # Convert normalized float coords to pixel coords
    points = []
    for lm in hand_landmarks:
        px, py = int(lm.x * w), int(lm.y * h)
        points.append((px, py))

    # Draw connections (lines)
    for connection in HAND_CONNECTIONS:
        pt1 = points[connection[0]]
        pt2 = points[connection[1]]
        cv2.line(frame, pt1, pt2, (255, 255, 255), 2)

    # Draw joints (circles)
    for pt in points:
        cv2.circle(frame, pt, 5, (0, 0, 255), -1)

    return points


def main():
    cam = Camera(0)
    model_path = "assets/models/hand_landmarker.task"
    landmarker = build_landmarker(model_path, _on_result)

    print("Starting perception spike. Press 'q' to quit.")

    with landmarker:
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                continue

            # Convert OpenCV BGR to MediaPipe RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Provide a strictly monotonic timestamp in milliseconds
            timestamp_ms = int(time.monotonic() * 1000)
            landmarker.detect_async(mp_image, timestamp_ms)

            try:
                # Pull the latest result from the callback thread
                result, result_frame, _ = result_queue.get(timeout=0.05)
                annotated_frame = cv2.cvtColor(result_frame, cv2.COLOR_RGB2BGR)

                # Draw landmarks if hands are detected
                if result.hand_landmarks:
                    for idx, hand_landmarks in enumerate(result.hand_landmarks):
                        # Draw custom skeleton and retrieve pixel points
                        points = draw_landmarks(annotated_frame, hand_landmarks)

                        # Render the handedness label at the wrist (landmark 0)
                        # Render the handedness label at the wrist (landmark 0)
                        if result.handedness and idx < len(result.handedness):
                            # The Tasks API returns a Category object for handedness
                            raw_label = result.handedness[idx][0].category_name

                            # Invert the label because we mirrored the frame before inference
                            corrected_label = "Left" if raw_label == "Right" else "Right"

                            wrist_coords = points[0]

                            cv2.putText(
                                annotated_frame,
                                corrected_label,
                                (wrist_coords[0] - 20, wrist_coords[1] + 30),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (0, 255, 0),
                                2,
                                cv2.LINE_AA,
                            )

                cv2.imshow("AirBluez Phase 1 Spike", annotated_frame)

            except queue.Empty:
                # If no result is ready, just show the raw frame
                cv2.imshow("AirBluez Phase 1 Spike", frame)

            # Break loop on 'q' key
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

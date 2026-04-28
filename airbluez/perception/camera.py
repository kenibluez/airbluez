import cv2
import numpy as np


class Camera:
    def __init__(self, camera_index: int = 0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera_index}")

    def read_frame(self) -> tuple[bool, np.ndarray]:
        ret, frame = self.cap.read()
        if not ret:
            return False, frame

        # Mirror the frame horizontally before inference
        # This ensures the model's "Left" hand matches the user's physical left hand
        mirrored = cv2.flip(frame, 1)
        return True, mirrored

    def release(self) -> None:
        self.cap.release()

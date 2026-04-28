import pygame

from airbluez.perception.schemas import HandFrame


class DebugOverlay:
    def draw_landmarks(
        self, surface: pygame.Surface, hand_frame: HandFrame, width: int, height: int
    ):
        """Draws the raw tracking skeleton over the webcam feed."""
        if not hand_frame or not hand_frame.landmarks_xy:
            return

        # Define connections (MediaPipe hand skeleton)
        connections = [
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
            (17, 18),
            (18, 19),
            (19, 20),  # Pinky
            (0, 17),  # Palm base
        ]

        # Convert normalized coordinates to pixel coordinates
        points = []
        for lm in hand_frame.landmarks_xy:
            px, py = int(lm[0] * width), int(lm[1] * height)
            points.append((px, py))

        # Draw lines
        color = (0, 255, 0) if hand_frame.handedness == "Left" else (0, 255, 255)
        for start_idx, end_idx in connections:
            pygame.draw.line(surface, color, points[start_idx], points[end_idx], 2)

        # Draw joints
        for px, py in points:
            pygame.draw.circle(surface, (255, 0, 0), (px, py), 4)

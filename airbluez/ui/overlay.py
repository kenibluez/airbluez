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
        color = (39, 132, 245) if hand_frame.handedness == "Left" else (245, 149, 29)
        for start_idx, end_idx in connections:
            pygame.draw.line(surface, color, points[start_idx], points[end_idx], 3)

        # Draw joints
        for px, py in points:
            pygame.draw.circle(surface, (142, 39, 245), (px, py), 5)

    def draw_anchor_tether(
        self,
        surface: pygame.Surface,
        hand_frame: HandFrame,
        wheel_center: tuple[int, int],
        width: int,
        height: int,
    ):
        """Draws a tether from the hand's tracking point to the wheel center."""
        if not hand_frame or not hand_frame.landmarks_xy:
            return

        # Landmark 9 is the Middle Finger MCP (center of palm)
        hx, hy = hand_frame.landmarks_xy[9]
        px, py = int(hx * width), int(hy * height)

        # 1. Draw the line to the center (Thin and semi-transparent)
        tether_color = (0, 255, 0, 150)
        pygame.draw.line(surface, tether_color, (px, py), wheel_center, 1)

        # 2. Draw a highlight circle at the hand center
        pygame.draw.circle(surface, (255, 255, 255), (px, py), 6, 2)  # Outer ring
        pygame.draw.circle(surface, (0, 255, 0), (px, py), 3)  # Inner dot

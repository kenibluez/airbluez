import math


class WheelMapper:
    def __init__(self, hysteresis_deg: float = 5.0):
        self.hysteresis = hysteresis_deg

        # New Custom Order: C to B (Naturals), then the Accidentals
        self.roots = ["C", "D", "E", "F", "G", "A", "B", "Db", "Eb", "Gb", "Ab", "Bb"]
        self.num_segments = len(self.roots)
        self.segment_size = 360.0 / self.num_segments
        self.current_root_idx = 0

    def get_root_from_position(
        self, hand_point: tuple[float, float], anchor: tuple[float, float] = (0.3, 0.5)
    ) -> str:
        hx, hy = hand_point
        ax, ay = anchor

        dx = hx - ax
        dy = hy - ay

        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)

        # Shift the angle so 180 degrees (Left) acts as our 0 index for the array
        angle_shifted = (angle_deg - 180) % 360

        raw_idx = (
            int((angle_shifted + (self.segment_size / 2)) // self.segment_size) % self.num_segments
        )

        # Hysteresis
        segment_center = raw_idx * self.segment_size
        diff = angle_shifted - segment_center

        if diff > 180:
            diff -= 360
        if diff < -180:
            diff += 360

        boundary_dist = (self.segment_size / 2) - abs(diff)

        if boundary_dist > self.hysteresis or self.current_root_idx == raw_idx:
            self.current_root_idx = raw_idx

        return self.roots[self.current_root_idx]

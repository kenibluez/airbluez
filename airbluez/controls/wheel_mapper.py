from typing import Optional

import numpy as np


class WheelMapper:
    def __init__(self, hysteresis_deg: float = 5.0):
        # Camelot Wheel ordering as per GESTURES.md
        self.roots = ["C", "G", "D", "A", "E", "B", "Gb", "Db", "Ab", "Eb", "Bb", "F"]
        self.num_segments = len(self.roots)
        self.segment_size = 360.0 / self.num_segments
        self.hysteresis = hysteresis_deg
        self.current_root_idx: Optional[int] = None

    def get_root_from_angle(
        self, wrist_xy: tuple[float, float], index_mcp_xy: tuple[float, float]
    ) -> str:
        """
        Calculates angle from wrist to index finger MCP and maps to chord root.
        Angles are normalized 0-360 degrees.
        """
        # Calculate vector from wrist to index MCP
        dx = index_mcp_xy[0] - wrist_xy[0]
        dy = index_mcp_xy[1] - wrist_xy[1]

        # Calculate angle in degrees (pointing up = 0 or 360)
        angle = np.degrees(np.arctan2(dx, -dy)) % 360

        # Initial assignment
        if self.current_root_idx is None:
            self.current_root_idx = (
                int((angle + (self.segment_size / 2)) / self.segment_size) % self.num_segments
            )
            return self.roots[self.current_root_idx]

        # Hysteresis logic: only switch if we've moved significantly into a new segment
        target_idx = int((angle + (self.segment_size / 2)) / self.segment_size) % self.num_segments

        if target_idx != self.current_root_idx:
            # Calculate how far we are from the boundary of the current segment
            current_center = self.current_root_idx * self.segment_size
            diff = abs((angle - current_center + 180) % 360 - 180)

            # Change only if outside the hysteresis buffer
            if diff > (self.segment_size / 2 + self.hysteresis):
                self.current_root_idx = target_idx

        return self.roots[self.current_root_idx]

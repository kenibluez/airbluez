from airbluez.controls.wheel_mapper import WheelMapper

def test_wheel_mapping_roots():
    mapper = WheelMapper()
    # Mock hand point relative to anchor (0.3, 0.5)
    # If anchor is (0.3, 0.5) and hand is at (0.4, 0.5), it's pointing right.
    # dx = 0.1, dy = 0. angle = 0. angle_shifted = (0-180)%360 = 180.
    # 180 / 30 = 6. Roots[6] is 'B'.
    root = mapper.get_root_from_position((0.4, 0.5), anchor=(0.3, 0.5))
    assert root == "B"

def test_hysteresis_prevention():
    """Ensure small jitters don't flip the root back and forth."""
    mapper = WheelMapper(hysteresis_deg=5.0)

    # Initial position: dx=0.1, dy=0 -> angle=0 -> shifted=180 -> root 'B' (idx 6)
    root = mapper.get_root_from_position((0.4, 0.5), anchor=(0.3, 0.5))
    assert root == "B"

    # Small jitter: move hand slightly, but stay within hysteresis (segment_size is 30 deg)
    # boundary_dist = 15 - abs(diff)
    # If we are at 180, diff=0, boundary_dist=15.
    # If we move to 190, diff=10, boundary_dist=5. Still > 5 (our hysteresis is 5.0) wait...
    # If boundary_dist > hysteresis, we update. 
    # Wait, the logic in WheelMapper is:
    # if boundary_dist > self.hysteresis or self.current_root_idx == raw_idx:
    #     self.current_root_idx = raw_idx
    
    # Let's test crossing a boundary.
    # Segment 6 is 180 center. Boundary is at 195.
    # At 194.5, raw_idx becomes 7.
    # angle_shifted = 194.5
    # raw_idx = int((194.5 + 15) // 30) = int(209.5 // 30) = 6. Still 6.
    
    # At 195.1:
    # raw_idx = int((195.1 + 15) // 30) = int(210.1 // 30) = 7.
    # segment_center = 7 * 30 = 210.
    # diff = 195.1 - 210 = -14.9.
    # boundary_dist = 15 - 14.9 = 0.1.
    # 0.1 < 5.0, so self.current_root_idx stays at 6!
    
    # Move to 195.1 deg shifted. 
    # dx = cos(15.1), dy = sin(15.1) roughly.
    import math
    angle_rad = math.radians(15.1)
    root = mapper.get_root_from_position((0.3 + 0.1*math.cos(angle_rad), 0.5 + 0.1*math.sin(angle_rad)), anchor=(0.3, 0.5))
    assert root == "B" # Should still be B due to hysteresis

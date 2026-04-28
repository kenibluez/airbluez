from airbluez.controls.wheel_mapper import WheelMapper


def test_wheel_mapping_roots():
    mapper = WheelMapper()
    # Mock wrist at 0,0 and index pointing right (90 degrees)
    # 90 degrees should be roughly segment 3 (D) if C is 0
    root = mapper.get_root_from_angle((0, 0), (1, 0))
    assert root in mapper.roots


def test_hysteresis_prevention():
    """Ensure small jitters don't flip the root back and forth."""
    mapper = WheelMapper(hysteresis_deg=5.0)

    # Set initial position in 'C' (0 degrees)
    mapper.get_root_from_angle((0, 0), (0, -1))
    original_root = mapper.roots[mapper.current_root_idx]

    # Move just slightly past the boundary (e.g., 16 degrees, where boundary is 15)
    # It should NOT change yet due to the 5-degree hysteresis buffer
    new_root = mapper.get_root_from_angle((0, 0), (0.28, -0.96))  # ~16.2 degrees
    assert new_root == original_root

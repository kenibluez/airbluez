import dataclasses


@dataclasses.dataclass
class HandFrame:
    handedness: str
    landmarks_xy: list[tuple[float, float]]
    landmarks_world: list[tuple[float, float, float]]
    timestamp_ms: int

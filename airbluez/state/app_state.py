from pidantic import BaseModel


class AppState(BaseModel):
    play: bool = False
    chord_root: str = "C"
    chord_quality: str = "major"
    sample_id: int = 0
    volume: float = 0.5

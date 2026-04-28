from airbluez.state.app_state import AppState


def apply_right_hand(
    state: AppState, sample_delta: int, new_volume: float, max_samples: int = 4
) -> AppState:
    """Pure function returning a new AppState based on right hand actions."""
    # Handle wrap-around for the sample bank index
    new_sample_id = (state.sample_id + sample_delta) % max_samples

    # Pydantic's model_copy(update=...) is the equivalent of dataclass replace
    return state.model_copy(update={"sample_id": new_sample_id, "volume": new_volume})


# (Keep your existing apply_right_hand function here)


def apply_left_hand(state: AppState, root: str, quality: str) -> AppState:
    """Pure function returning a new AppState based on left hand chord changes."""
    return state.model_copy(update={"chord_root": root, "chord_quality": quality})


def apply_play_pause(state: AppState, play: bool) -> AppState:
    """Pure function to toggle the play state."""
    return state.model_copy(update={"play": play})

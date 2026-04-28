from airbluez.state.app_state import AppState


def apply_right_hand(
    state: AppState, sample_delta: int, new_volume: float, max_samples: int = 4
) -> AppState:
    """Pure function returning a new AppState based on right hand actions."""
    # Handle wrap-around for the sample bank index
    new_sample_id = (state.sample_id + sample_delta) % max_samples

    # Pydantic's model_copy(update=...) is the equivalent of dataclass replace
    return state.model_copy(update={"sample_id": new_sample_id, "volume": new_volume})

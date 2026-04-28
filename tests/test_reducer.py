from airbluez.state.app_state import AppState
from airbluez.state.reducer import apply_left_hand, apply_play_pause
from airbluez.state.store import Store


def test_apply_left_hand():
    """Ensure the reducer safely copies and updates the left hand state."""
    initial = AppState(chord_root="C", chord_quality="major")

    # Change to G minor
    updated = apply_left_hand(initial, "G", "minor")

    # Verify new state
    assert updated.chord_root == "G"
    assert updated.chord_quality == "minor"

    # Verify original state wasn't mutated (purity check)
    assert initial.chord_root == "C"


def test_store_subscription():
    """Ensure the Store alerts subscribers when state changes."""
    store = Store(AppState())

    # We'll use a list to capture events inside the callback
    events = []
    store.subscribe(lambda old, new: events.append((old, new)))

    # Dispatch a play state change
    new_state = apply_play_pause(store.state, True)
    store.dispatch(new_state)

    assert len(events) == 1
    assert events[0][0].play is False  # Old state
    assert events[0][1].play is True  # New state

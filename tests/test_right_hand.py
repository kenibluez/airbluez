import time
from airbluez.controls.right_hand import RightHandController
from airbluez.state.app_state import AppState
from airbluez.state.reducer import apply_right_hand

def test_volume_clamping():
    """Ensure vertical delta volume is clamped strictly to [0, 1]."""
    ctrl = RightHandController(volume_k=1.0)
    
    # Hand starts at Y=0.5
    ctrl.process("index_left", 0.5, 0.5)
    
    # Move hand WAY down (Y=1.5, massive positive delta). Volume should drop to 0.
    _, vol = ctrl.process("index_left", 0.5, 1.5)
    assert vol == 0.0
    
    # Move hand WAY up (Y=-1.0, massive negative delta). Volume should max out at 1.0.
    _, vol = ctrl.process("index_left", 0.5, -1.0)
    assert vol == 1.0

def test_swipe_debounce_and_reducer(monkeypatch):
    """Ensure a swipe triggers a sample change but locks out immediately after."""
    ctrl = RightHandController(swipe_threshold=0.1, debounce_sec=0.3)
    state = AppState(sample_id=0)
    
    # Mock time so we can control the 0.3s debounce window
    current_time = 100.0
    monkeypatch.setattr(time, "time", lambda: current_time)
    
    # Frame 1: Hand at origin
    ctrl.process("index_up", 0.0, 0.5)
    
    # Frame 2 (0.1s later): Fast swipe right (dx = 0.2)
    current_time = 100.1
    delta, vol = ctrl.process("index_up", 0.2, 0.5)
    assert delta == 1
    
    # Pass through pure reducer
    state = apply_right_hand(state, delta, vol, max_samples=4)
    assert state.sample_id == 1
    
    # Frame 3 (0.2s later, still inside debounce): Another swipe right
    current_time = 100.2
    # Seed new history origin
    ctrl.process("index_up", 0.2, 0.5)
    
    current_time = 100.3
    delta, vol = ctrl.process("index_up", 0.4, 0.5) # dx = 0.2 again
    # Delta should be 0 because 100.3 - 100.1 < 0.3s
    assert delta == 0
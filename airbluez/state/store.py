from typing import Callable, List

from airbluez.state.app_state import AppState


class Store:
    def __init__(self, initial_state: AppState):
        self.state = initial_state
        # List of callbacks that expect (old_state, new_state)
        self.subscribers: List[Callable[[AppState, AppState], None]] = []

    def subscribe(self, callback: Callable[[AppState, AppState], None]):
        """Register a function to be called whenever the state changes."""
        self.subscribers.append(callback)

    def dispatch(self, new_state: AppState):
        """Updates the central state and notifies all subscribers."""
        # Only notify if something actually changed to prevent infinite loops
        if self.state != new_state:
            old_state = self.state
            self.state = new_state

            for sub in self.subscribers:
                sub(old_state, new_state)

import time
from collections import deque


class RightHandController:
    def __init__(
        self,
        swipe_threshold: float = 0.15,
        volume_k: float = 1.0,
        debounce_sec: float = 0.3,
        window_sec: float = 0.5,
    ):
        self.swipe_threshold = swipe_threshold
        self.volume_k = volume_k
        self.debounce_sec = debounce_sec
        self.window_sec = window_sec

        # Buffer to store (x, y, timestamp) for the 0.5s window
        self.history = deque()
        self.last_swipe_time = 0.0

        # Local state tracker for volume to apply continuous deltas
        self.current_volume = 0.5

    def process(self, gesture: str, tip_x: float, tip_y: float) -> tuple[int, float]:
        """
        Returns (sample_delta, new_volume).
        sample_delta is -1, 0, or 1.
        """
        current_time = time.time()
        self.history.append((tip_x, tip_y, current_time))

        # Prune history older than the 0.5s window
        while self.history and (current_time - self.history[0][2]) > self.window_sec:
            self.history.popleft()

        sample_delta = 0

        if not self.history:
            return sample_delta, self.current_volume

        # Calculate deltas
        # For swipes, we check the delta across the whole 0.5s window
        oldest_x = self.history[0][0]
        dx = tip_x - oldest_x

        # For volume, frame-to-frame delta is smoother than the whole window
        old_y = self.history[-2][1] if len(self.history) > 1 else tip_y
        dy = tip_y - old_y

        if gesture == "index_up":
            # Track horizontal swipe[cite: 1]
            if abs(dx) > self.swipe_threshold:
                if (current_time - self.last_swipe_time) > self.debounce_sec:
                    # Positive dx = swipe right, Negative dx = swipe left
                    sample_delta = 1 if dx > 0 else -1
                    self.last_swipe_time = current_time
                    self.history.clear()  # Flush window so we don't double-trigger

        elif gesture == "index_left":
            # Track vertical delta for volume[cite: 1]
            # Camera Y is 0 at top, 1 at bottom. Moving hand UP = negative dy.
            # To make UP increase volume, we invert dy.
            vol_change = -dy * self.volume_k
            # Clamp volume between [0, 1][cite: 1]
            self.current_volume = max(0.0, min(1.0, self.current_volume + vol_change))

        return sample_delta, self.current_volume

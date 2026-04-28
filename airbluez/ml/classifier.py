import os
from collections import Counter, deque

import joblib


class GestureClassifier:
    def __init__(self, hand: str, window_size: int = 5):
        model_path = f"airbluez/ml/models/{hand}_gesture.joblib"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}. Run train.py first.")

        self.model = joblib.load(model_path)
        # Ring buffer for temporal smoothing as per GESTURES.md
        self.history = deque(maxlen=window_size)

    def predict(self, feature_vector: list[float]) -> str:
        # Get raw prediction
        prediction = self.model.predict([feature_vector])[0]
        self.history.append(prediction)

        # Majority vote smoothing
        most_common = Counter(self.history).most_common(1)
        return most_common[0][0]

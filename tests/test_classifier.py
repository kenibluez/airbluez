from unittest.mock import MagicMock

from airbluez.ml.classifier import GestureClassifier


def test_majority_vote_smoothing():
    """The classifier should return the most frequent gesture in its window."""
    # Mock the internal model to avoid loading a real .joblib
    classifier = GestureClassifier("left", window_size=3)
    classifier.model = MagicMock()

    # Mock sequence: A, B, A
    classifier.model.predict.side_effect = [["open"], ["closed"], ["open"]]

    # Frame 1: History [open] -> Output: open
    assert classifier.predict([0] * 100) == "open"
    # Frame 2: History [open, closed] -> Output: open (first in tie or majority)
    assert classifier.predict([0] * 100) == "open"
    # Frame 3: History [open, closed, open] -> Output: open
    assert classifier.predict([0] * 100) == "open"

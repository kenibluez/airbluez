import numpy as np

from airbluez.perception.features import extract_features
from airbluez.perception.schemas import HandFrame


def test_feature_translation_invariance():
    """Features should be the same even if the hand is shifted in space."""
    # Create a dummy hand (landmarks)
    landmarks = [[0.0, 0.0, 0.0]] * 21
    landmarks[9] = [0.0, 0.5, 0.0]  # Middle MCP for scaling

    frame1 = HandFrame("Left", landmarks, landmarks, 0)

    # Shifted hand (add 10.0 to every coordinate)
    shifted_landmarks = (np.array(landmarks) + 10.0).tolist()
    frame2 = HandFrame("Left", shifted_landmarks, shifted_landmarks, 0)

    feat1 = extract_features(frame1)
    feat2 = extract_features(frame2)

    # Check if vectors are almost identical
    assert np.allclose(feat1, feat2, atol=1e-5)


def test_feature_scale_invariance():
    """Features should be the same even if the hand is twice as large."""
    landmarks = [[0.0, 0.0, 0.0]] * 21
    landmarks[9] = [0.0, 0.5, 0.0]
    frame1 = HandFrame("Left", landmarks, landmarks, 0)

    # Scaled hand (2x)
    scaled_landmarks = (np.array(landmarks) * 2.0).tolist()
    frame2 = HandFrame("Left", scaled_landmarks, scaled_landmarks, 0)

    feat1 = extract_features(frame1)
    feat2 = extract_features(frame2)

    assert np.allclose(feat1, feat2, atol=1e-5)

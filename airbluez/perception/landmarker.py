# pyright: reportInvalidTypeForm=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportMissingTypeStubs=false
# pyright: reportExplicitAny=false

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

if TYPE_CHECKING:
    from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerResult


def build_landmarker(
    model_path: str,
    result_callback: Callable[[HandLandmarkerResult, mp.Image, int], None],
) -> HandLandmarker:
    base_options = mp_python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.LIVE_STREAM,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        result_callback=result_callback,
    )
    return vision.HandLandmarker.create_from_options(options)

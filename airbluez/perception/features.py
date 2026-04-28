import numpy as np

from airbluez.perception.schemas import HandFrame


def extract_features(hand_frame: HandFrame) -> list[float]:
    """
    Translates landmarks so wrist = origin, scales by middle-finger MCP distance,
    and computes geometric features.
    """
    # Use 3D world landmarks for scale-invariant geometry
    coords = np.array(hand_frame.landmarks_world)

    # 1. Translation: Wrist (index 0) becomes origin
    wrist = coords[0]
    translated = coords - wrist

    # 2. Scaling: Normalize by distance from wrist to Middle MCP (index 9)
    middle_mcp = translated[9]
    scale = np.linalg.norm(middle_mcp)
    # Prevent division by zero just in case
    if scale < 1e-6:
        scale = 1e-6
    normalized = translated / scale

    # 3. Compute Finger-Extended Booleans
    # A simple heuristic: is the fingertip further from the wrist than the PIP joint?
    # Indices: Thumb(4 vs 2), Index(8 vs 6), Middle(12 vs 10), Ring(16 vs 14), Pinky(20 vs 18)
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18]
    extended_bools = []
    for tip, pip in zip(tips, pips):
        tip_dist = np.linalg.norm(normalized[tip])
        pip_dist = np.linalg.norm(normalized[pip])
        extended_bools.append(1.0 if tip_dist > pip_dist else 0.0)

    # 4. Fingertip Pairwise Distances (distances between 4, 8, 12, 16, 20)
    tip_coords = normalized[tips]
    pairwise_distances = []
    for i in range(len(tips)):
        for j in range(i + 1, len(tips)):
            dist = np.linalg.norm(tip_coords[i] - tip_coords[j])
            pairwise_distances.append(dist)

    # 5. Wrist -> Index Angle (simplified to angle in XY plane relative to vertical)
    index_mcp = normalized[5]
    wrist_to_index_angle = np.arctan2(index_mcp[1], index_mcp[0])

    # Flatten normalized coordinates and append the computed features
    feature_vector = normalized.flatten().tolist()
    feature_vector.extend(extended_bools)
    feature_vector.extend(pairwise_distances)
    feature_vector.append(float(wrist_to_index_angle))

    return feature_vector


def get_feature_names() -> list[str]:
    """Returns headers for the CSV file."""
    names = [f"norm_{i}_{axis}" for i in range(21) for axis in ["x", "y", "z"]]
    names.extend([f"ext_{finger}" for finger in ["thumb", "index", "middle", "ring", "pinky"]])

    tips = ["thumb", "index", "middle", "ring", "pinky"]
    names.extend(
        [f"dist_{tips[i]}_{tips[j]}" for i in range(len(tips)) for j in range(i + 1, len(tips))]
    )
    names.append("wrist_index_angle")
    return names

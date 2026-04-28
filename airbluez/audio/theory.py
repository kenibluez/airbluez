# Frequencies for the 4th octave (A4 = 440Hz)
NOTE_FREQS = {
    "C": 261.63,
    "Gb": 369.99,
    "G": 392.00,
    "Db": 277.18,
    "D": 293.66,
    "Ab": 415.30,
    "A": 440.00,
    "Eb": 311.13,
    "E": 329.63,
    "Bb": 466.16,
    "B": 493.88,
    "F": 349.23,
}

# Intervals relative to root (in semitones)
CHORD_QUALITIES = {
    "major": [0, 4, 7, 12],
    "minor": [0, 3, 7, 12],
    "dim": [0, 3, 6, 12],
    "aug": [0, 4, 8, 12],
    "maj7": [0, 4, 7, 11],
    "pinch": [0, 5, 7, 12],  # Suspended 4th
}


def get_chord_frequencies(root: str, quality: str) -> list[float]:
    """Returns a list of frequencies for the given chord."""
    base_freq = NOTE_FREQS.get(root, 261.63)
    intervals = CHORD_QUALITIES.get(quality, CHORD_QUALITIES["major"])

    # Calculate frequencies: f = root * 2^(n/12)
    return [base_freq * (2 ** (n / 12)) for n in intervals]

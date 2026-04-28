from airbluez.audio.theory import get_chord_frequencies


def test_major_chord_intervals():
    # A4 is 440Hz. Major third is 4 semitones up.
    # 440 * 2^(4/12) ≈ 554.37
    freqs = get_chord_frequencies("A", "major")
    assert round(freqs[0], 2) == 440.00
    assert round(freqs[1], 2) == 554.37


def test_minor_chord_intervals():
    # A4 minor third is 3 semitones up.
    # 440 * 2^(3/12) ≈ 523.25
    freqs = get_chord_frequencies("A", "minor")
    assert round(freqs[1], 2) == 523.25

from pyo import LFO, Blit, Sine, SuperSaw


class SampleBank:
    """Manages synthesizer presets and timbres."""

    def __init__(self):
        self.presets = ["pad", "rhodes", "piano", "guitar"]
        self.current_idx = 0

    def get_current_preset(self) -> str:
        return self.presets[self.current_idx]

    def next_preset(self) -> str:
        self.current_idx = (self.current_idx + 1) % len(self.presets)
        return self.get_current_preset()

    def build_synth_voice(self, freqs: list[float], mul) -> object:
        """Returns a Pyo synth object based on the current preset."""
        preset = self.get_current_preset()

        # Pad: Smooth sine waves
        if preset == "pad":
            return Sine(freq=freqs, mul=mul)

        # Rhodes: Triangle-like LFO
        elif preset == "rhodes":
            return LFO(freq=freqs, type=3, mul=mul)

        # Piano/Keys: Slightly richer harmonics
        elif preset == "piano":
            return Blit(freq=freqs, harms=5, mul=mul)

        # Guitar: Sawtooth for a plucked/strummed edge
        elif preset == "guitar":
            return SuperSaw(freq=freqs, detune=0.5, mul=mul)

        return Sine(freq=freqs, mul=mul)

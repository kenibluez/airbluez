from pyo import Blit, LFO, Sine, SuperSaw


class SampleBank:
    """Manages synthesizer presets and timbres."""

    def __init__(self):
        self.presets = ["squarewave", "synthwave", "pad", "sawtooth"]
        self.current_idx = 0

    def get_current_preset(self) -> str:
        return self.presets[self.current_idx]

    def next_preset(self) -> str:
        self.current_idx = (self.current_idx + 1) % len(self.presets)
        return self.get_current_preset()

    def build_synth_voice(self, freqs: list[float], mul) -> object:
        """Returns a Pyo synth object based on the current preset."""
        preset = self.get_current_preset()

        # Squarewave: LFO type 2 is square
        if preset == "squarewave":
            return LFO(freq=freqs, type=2, mul=mul)

        # Synthwave: Thick SuperSaw
        elif preset == "synthwave":
            return SuperSaw(freq=freqs, detune=0.6, bal=0.5, mul=mul)

        # Pad: Smooth Sine with some harmonics if needed, but Sine is classic pad base
        elif preset == "pad":
            return Sine(freq=freqs, mul=mul)

        # Sawtooth: Blit with many harmonics
        elif preset == "sawtooth":
            return Blit(freq=freqs, harms=20, mul=mul)

        return Sine(freq=freqs, mul=mul)

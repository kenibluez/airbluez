from pyo import Fader

from airbluez.audio.sample_bank import SampleBank
from airbluez.audio.theory import get_chord_frequencies


class ChordPlayer:
    def __init__(self, sample_bank: SampleBank, crossfade_ms: int = 50):
        self.bank = sample_bank
        self.crossfade_sec = crossfade_ms / 1000.0

        # We need two voices to crossfade between A and B
        self.active_voice = 0
        self.faders = [
            Fader(fadein=self.crossfade_sec, fadeout=self.crossfade_sec, dur=0),
            Fader(fadein=self.crossfade_sec, fadeout=self.crossfade_sec, dur=0),
        ]

        # Initialize empty synth voices
        self.synths = [
            self.bank.build_synth_voice([0, 0, 0, 0], mul=self.faders[0]),
            self.bank.build_synth_voice([0, 0, 0, 0], mul=self.faders[1]),
        ]

        self.current_chord = (None, None)
        self.is_playing = False

    def play(self, root: str, quality: str, volume: float = 0.5):
        """Crossfades to a new chord."""
        if not root or not quality:
            self.stop()
            return

        self.is_playing = True

        if (root, quality) == self.current_chord:
            # If chord is the same, just ensure it's fading in/playing
            self.faders[self.active_voice].play()
            return

        # Prepare the next voice
        next_voice = 1 - self.active_voice
        new_freqs = get_chord_frequencies(root, quality)

        # Update synth frequencies (and rebuild if preset changed)
        self.synths[next_voice].stop()
        self.synths[next_voice] = self.bank.build_synth_voice(
            new_freqs, mul=self.faders[next_voice] * volume
        )
        self.synths[next_voice].out()

        # Crossfade: Fade in next, fade out current
        self.faders[next_voice].play()
        self.faders[self.active_voice].stop()

        self.active_voice = next_voice
        self.current_chord = (root, quality)

    def stop(self):
        """Fades out the current chord."""
        if self.is_playing:
            self.faders[self.active_voice].stop()
            self.is_playing = False
            self.current_chord = (None, None)

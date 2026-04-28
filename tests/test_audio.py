import time

from airbluez.audio.chord_player import ChordPlayer
from airbluez.audio.engine import AudioEngine
from airbluez.audio.sample_bank import SampleBank


def main():
    engine = AudioEngine()
    engine.start()

    bank = SampleBank()
    player = ChordPlayer(bank, crossfade_ms=50)

    try:
        print(f"Playing Preset: {bank.get_current_preset()}")

        print("Playing C Major...")
        player.play("C", "major")
        time.sleep(2)

        print("Crossfading to F major...")
        player.play("F", "major")
        time.sleep(2)

        print("Crossfading to G major...")
        player.play("G", "major")
        time.sleep(2)

        print("Fading out...")
        player.stop()
        time.sleep(1)  # Let the fadeout finish

    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()


if __name__ == "__main__":
    main()

import time

import pyo


def main():
    # Get all available audio output devices
    devices, indexes = pyo.pa_get_output_devices()
    default_idx = pyo.pa_get_default_output()

    print("=== AVAILABLE AUDIO OUTPUTS ===")
    for i in range(len(devices)):
        is_default = " (DEFAULT)" if indexes[i] == default_idx else ""
        print(f"Index [{indexes[i]}]: {devices[i]}{is_default}")

    print("\nBooting server on default device...")

    # Initialize server
    s = pyo.Server(duplex=0)
    s.boot()
    s.start()

    print("Playing a 440Hz test tone for 3 seconds. Listen closely!")
    # Create a simple sine wave and output it
    test_tone = pyo.Sine(freq=440, mul=0.2).out()

    time.sleep(3)
    s.stop()
    print("Test complete.")


if __name__ == "__main__":
    main()

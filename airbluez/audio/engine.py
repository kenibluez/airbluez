from pyo import Server


class AudioEngine:
    def __init__(self):
        # We drop the audio="alsa" argument and explicitly tell it
        # to use the PulseAudio virtual output (Index 11 from your test)
        self.server = Server(duplex=0)
        self.server.setOutputDevice(11)

    def start(self):
        self.server.boot()
        self.server.start()
        print("Pyo Audio Server started.")

    def stop(self):
        self.server.stop()
        self.server.shutdown()
        print("Pyo Audio Server stopped.")

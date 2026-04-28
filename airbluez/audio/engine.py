from pyo import Server


class AudioEngine:
    def __init__(self):
        self.server = Server(duplex=0)
        # Using duplex=0 prevents pyo from trying to grab microphone inputs,
        # which often causes ALSA/PortAudio crashes on Linux.

    def start(self):
        self.server.boot()
        self.server.start()
        print("Pyo Audio Server started.")

    def stop(self):
        self.server.stop()
        self.server.shutdown()
        print("Pyo Audio Server stopped.")

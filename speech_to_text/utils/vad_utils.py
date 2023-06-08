import webrtcvad


class VadWrapper:
    def __init__(self):
        self.vad = webrtcvad.Vad(3)
        self.RATE = 16000
        self.SILENT_CHUNKS_THRESHOLD = 20

    def is_speech(self, in_data):
        return self.vad.is_speech(in_data, self.RATE)

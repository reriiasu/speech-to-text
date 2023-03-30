from faster_whisper import WhisperModel


class WhisperModelWrapper:
    def __init__(self):
        self.model_size = "large-v2"
        self.model = WhisperModel(
            self.model_size, device="cuda", compute_type="float16"
        )

    def transcribe(self, audio):
        segments, _ = self.model.transcribe(
            audio=audio, beam_size=5, language="ja", word_timestamps=True
        )
        return segments

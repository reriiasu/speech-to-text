import asyncio
import queue
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pyaudio

from audio_utils import create_audio_stream
from vad_utils import VadWrapper
from whisper_utils import WhisperModelWrapper


class AudioTranscriber:
    def __init__(self):
        self.model_wrapper = WhisperModelWrapper()
        self.vad_wrapper = VadWrapper()
        self.silent_chunks = 0
        self.speech_buffer = []
        self.audio_queue = queue.Queue()

    async def transcribe_audio(self):
        with ThreadPoolExecutor() as executor:
            while True:
                audio_data_np = await asyncio.get_event_loop().run_in_executor(
                    executor, self.audio_queue.get
                )
                segments = await asyncio.get_event_loop().run_in_executor(
                    executor, self.model_wrapper.transcribe, audio_data_np
                )

                for segment in segments:
                    print(
                        f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}"
                    )

    def process_audio(self, in_data, frame_count, time_info, status):
        is_speech = self.vad_wrapper.is_speech(in_data)

        if is_speech:
            self.silent_chunks = 0
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.speech_buffer.append(audio_data)
        else:
            self.silent_chunks += 1

        if (
            not is_speech
            and self.silent_chunks > self.vad_wrapper.SILENT_CHUNKS_THRESHOLD
        ):

            if len(self.speech_buffer) > 0:
                audio_data_np = np.concatenate(self.speech_buffer)
                self.speech_buffer.clear()
                self.audio_queue.put(audio_data_np)

        return (in_data, pyaudio.paContinue)

    def start_transcription(self, selected_device_index):
        stream = create_audio_stream(selected_device_index, self.process_audio)
        print("Listening...")
        asyncio.run(self.transcribe_audio())
        stream.start_stream()
        try:
            while True:
                key = input("Enterキーを押したら終了します\n")
                if not key:
                    break
        except KeyboardInterrupt:
            print("Interrupted.")
        finally:
            stream.stop_stream()
            stream.close()

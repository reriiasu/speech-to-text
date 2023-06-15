import asyncio
import functools
import eel
import queue
import numpy as np

from typing import NamedTuple
from faster_whisper import WhisperModel
from concurrent.futures import ThreadPoolExecutor
from .utils.audio_utils import create_audio_stream
from .utils.vad_utils import VadWrapper


class AppOptions(NamedTuple):
    audio_device: int
    silence_limit: int = 8
    noise_threshold: int = 15


class AudioTranscriber:
    def __init__(
        self, event_loop: asyncio.AbstractEventLoop,
        whisper_model: WhisperModel,
        transcribe_settings: dict,
        app_options: AppOptions
    ):
        self.event_loop = event_loop
        self.whisper_model: WhisperModel = whisper_model
        self.transcribe_settings = transcribe_settings
        self.app_options = app_options
        self.vad_wrapper = VadWrapper()
        self.silence_counter: int = 0
        self.speech_buffer = []
        self.audio_queue = queue.Queue()
        self.transcribing = False
        self.stream = None
        self._running = asyncio.Event()
        self._transcribe_task = None

    async def transcribe_audio(self):
        with ThreadPoolExecutor() as executor:
            while self.transcribing:
                if not self.transcribing:
                    break
                try:
                    # Get audio data from queue with a timeout
                    audio_data_np = await self.event_loop.run_in_executor(executor, functools.partial(self.audio_queue.get, timeout=3.0))

                    # Create a partial function for the model's transcribe method
                    func = functools.partial(
                        self.whisper_model.transcribe, audio=audio_data_np, **self.transcribe_settings)

                    # Run the transcribe method in a thread
                    segments, _ = await self.event_loop.run_in_executor(executor, func)

                    for segment in segments:
                        eel.display_transcription(segment.text)

                except queue.Empty:
                    # Skip to the next iteration if a timeout occurs
                    continue
                except Exception as e:
                    for arg in e.args:
                        eel.on_recive_message(arg)

    def process_audio(self, indata, frames, time, status):
        indataBytes = indata.tobytes()
        is_speech = self.vad_wrapper.is_speech(indataBytes)
        if is_speech:
            self.silence_counter = 0
            audio_data = np.frombuffer(indataBytes, dtype=np.int16)
            self.speech_buffer.append(audio_data)
        else:
            self.silence_counter += 1

        if (
            not is_speech
            and self.silence_counter > self.app_options.silence_limit
        ):
            if len(self.speech_buffer) > self.app_options.noise_threshold:
                audio_data_np = np.concatenate(self.speech_buffer)
                self.speech_buffer.clear()
                self.audio_queue.put(audio_data_np)
            else:
                # noise clear
                self.speech_buffer.clear()

    async def start_transcription(self):
        try:
            self.transcribing = True
            self.stream = create_audio_stream(
                self.app_options.audio_device, self.process_audio)
            self.stream.start()
            self._running.set()
            self._transcribe_task = asyncio.run_coroutine_threadsafe(
                self.transcribe_audio(), self.event_loop)
            eel.on_recive_message("Transcription started.")
            while self._running.is_set():
                await asyncio.sleep(1)
        except Exception as e:
            for arg in e.args:
                eel.on_recive_message(arg)

    async def stop_transcription(self):
        try:
            self.transcribing = False
            if self._transcribe_task is not None:
                self.event_loop.call_soon_threadsafe(
                    self._transcribe_task.cancel)
                self._transcribe_task = None

            if self.stream is not None:
                self._running.clear()
                self.stream.stop()
                self.stream.close()
                self.stream = None
                eel.on_recive_message("Transcription stopped.")
            else:
                eel.on_recive_message("No active stream to stop.")
        except Exception as e:
            print(e)
            for arg in e.args:
                eel.on_recive_message(arg)

import asyncio
import functools
import eel
import queue
import numpy as np

from typing import NamedTuple
from faster_whisper import WhisperModel
from concurrent.futures import ThreadPoolExecutor
from .utils.audio_utils import create_audio_stream
from .utils.vad_utils import VadUtils
from .utils.file_utils import write_audio


class AppOptions(NamedTuple):
    audio_device: int
    silence_limit: int = 8
    noise_threshold: int = 5
    create_audio_file: bool = True


class AudioTranscriber:
    def __init__(
        self,
        event_loop: asyncio.AbstractEventLoop,
        whisper_model: WhisperModel,
        transcribe_settings: dict,
        app_options: AppOptions,
    ):
        self.event_loop = event_loop
        self.whisper_model: WhisperModel = whisper_model
        self.transcribe_settings = transcribe_settings
        self.app_options = app_options
        self.vad_wrapper = VadUtils()
        self.silence_counter: int = 0
        self.audio_data_list = []
        self.all_audio_data_list = []
        self.audio_queue = queue.Queue()
        self.transcribing = False
        self.stream = None
        self._running = asyncio.Event()
        self._transcribe_task = None

    async def transcribe_audio(self):
        with ThreadPoolExecutor() as executor:
            while self.transcribing:
                try:
                    # Get audio data from queue with a timeout
                    audio_data = await self.event_loop.run_in_executor(
                        executor, functools.partial(self.audio_queue.get, timeout=3.0)
                    )

                    # Create a partial function for the model's transcribe method
                    func = functools.partial(
                        self.whisper_model.transcribe,
                        audio=audio_data,
                        **self.transcribe_settings,
                    )

                    # Run the transcribe method in a thread
                    segments, _ = await self.event_loop.run_in_executor(executor, func)

                    for segment in segments:
                        eel.display_transcription(segment.text)

                except queue.Empty:
                    # Skip to the next iteration if a timeout occurs
                    continue
                except Exception as e:
                    eel.on_recive_message(str(e))

    def process_audio(self, audio_data: np.ndarray, frames: int, time, status):
        is_speech = self.vad_wrapper.is_speech(audio_data)
        if is_speech:
            self.silence_counter = 0
            self.audio_data_list.append(audio_data.flatten())
        else:
            self.silence_counter += 1

        if not is_speech and self.silence_counter > self.app_options.silence_limit:
            self.silence_counter = 0

            if self.app_options.create_audio_file:
                self.all_audio_data_list.extend(self.audio_data_list)

            if len(self.audio_data_list) > self.app_options.noise_threshold:
                concatenate_audio_data = np.concatenate(self.audio_data_list)
                self.audio_data_list.clear()
                self.audio_queue.put(concatenate_audio_data)
            else:
                # noise clear
                self.audio_data_list.clear()

    def batch_transcribe_audio(self, audio_data: np.ndarray):
        segment_list = []

        segments, _ = self.whisper_model.transcribe(
            audio=audio_data, **self.transcribe_settings
        )

        for segment in segments:
            segment_list.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}",
                }
            )
        eel.on_recive_segments(segment_list)

    async def start_transcription(self):
        try:
            self.transcribing = True
            self.stream = create_audio_stream(
                self.app_options.audio_device, self.process_audio
            )
            self.stream.start()
            self._running.set()
            self._transcribe_task = asyncio.run_coroutine_threadsafe(
                self.transcribe_audio(), self.event_loop
            )
            eel.on_recive_message("Transcription started.")
            while self._running.is_set():
                await asyncio.sleep(1)
        except Exception as e:
            eel.on_recive_message(str(e))

    async def stop_transcription(self):
        try:
            self.transcribing = False
            if self._transcribe_task is not None:
                self.event_loop.call_soon_threadsafe(self._transcribe_task.cancel)
                self._transcribe_task = None

            if self.app_options.create_audio_file and len(self.all_audio_data_list) > 0:
                audio_data = np.concatenate(self.all_audio_data_list)
                self.all_audio_data_list.clear()
                write_audio("web", "voice", audio_data)
                self.batch_transcribe_audio(audio_data)

            if self.stream is not None:
                self._running.clear()
                self.stream.stop()
                self.stream.close()
                self.stream = None
                eel.on_recive_message("Transcription stopped.")
            else:
                eel.on_recive_message("No active stream to stop.")
        except Exception as e:
            eel.on_recive_message(str(e))

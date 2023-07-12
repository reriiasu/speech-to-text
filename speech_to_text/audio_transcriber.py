import asyncio
import functools
import eel
import queue
import numpy as np

from typing import NamedTuple
from faster_whisper import WhisperModel
from concurrent.futures import ThreadPoolExecutor

from .utils.audio_utils import create_audio_stream
from .vad import Vad
from .utils.file_utils import write_audio
from .websoket_server import WebSocketServer
from .openai_api import OpenAIAPI


class AppOptions(NamedTuple):
    audio_device: int
    silence_limit: int = 8
    noise_threshold: int = 5
    non_speech_threshold: float = 0.1
    include_non_speech: bool = False
    create_audio_file: bool = True
    use_websocket_server: bool = False
    use_openai_api: bool = False


class AudioTranscriber:
    def __init__(
        self,
        event_loop: asyncio.AbstractEventLoop,
        whisper_model: WhisperModel,
        transcribe_settings: dict,
        app_options: AppOptions,
        websocket_server: WebSocketServer,
        openai_api: OpenAIAPI,
    ):
        self.event_loop = event_loop
        self.whisper_model: WhisperModel = whisper_model
        self.transcribe_settings = transcribe_settings
        self.app_options = app_options
        self.websocket_server = websocket_server
        self.openai_api = openai_api
        self.vad = Vad(app_options.non_speech_threshold)
        self.silence_counter: int = 0
        self.audio_data_list = []
        self.all_audio_data_list = []
        self.audio_queue = queue.Queue()
        self.transcribing = False
        self.stream = None
        self._running = asyncio.Event()
        self._transcribe_task = None

    async def transcribe_audio(self):
        # Ignore parameters that affect performance
        transcribe_settings = self.transcribe_settings.copy()
        transcribe_settings["without_timestamps"] = True
        transcribe_settings["word_timestamps"] = False

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
                        **transcribe_settings,
                    )

                    # Run the transcribe method in a thread
                    segments, _ = await self.event_loop.run_in_executor(executor, func)

                    for segment in segments:
                        eel.display_transcription(segment.text)
                        if self.websocket_server is not None:
                            await self.websocket_server.send_message(segment.text)

                except queue.Empty:
                    # Skip to the next iteration if a timeout occurs
                    continue
                except Exception as e:
                    eel.on_recive_message(str(e))

    def process_audio(self, audio_data: np.ndarray, frames: int, time, status):
        is_speech = self.vad.is_speech(audio_data)
        if is_speech:
            self.silence_counter = 0
            self.audio_data_list.append(audio_data.flatten())
        else:
            self.silence_counter += 1
            if self.app_options.include_non_speech:
                self.audio_data_list.append(audio_data.flatten())

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
            word_list = []
            if self.transcribe_settings["word_timestamps"] == True:
                for word in segment.words:
                    word_list.append(
                        {
                            "start": word.start,
                            "end": word.end,
                            "text": word.word,
                        }
                    )
            segment_list.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": word_list,
                }
            )

        eel.transcription_clear()

        if self.openai_api is not None:
            self.text_proofreading(segment_list)
        else:
            eel.on_recive_segments(segment_list)

    def text_proofreading(self, segment_list: list):
        # Use [#] as a separator
        combined_text = "[#]" + "[#]".join(segment["text"] for segment in segment_list)
        result = self.openai_api.text_proofreading(combined_text)
        split_text = result.split("[#]")

        del split_text[0]

        eel.display_transcription("Before text proofreading.")
        eel.on_recive_segments(segment_list)

        if len(split_text) == len(segment_list):
            for i, segment in enumerate(segment_list):
                segment["text"] = split_text[i]
                segment["words"] = []
            eel.on_recive_message("proofread success.")
            eel.display_transcription("After text proofreading.")
            eel.on_recive_segments(segment_list)
        else:
            eel.on_recive_message("proofread failure.")
            eel.on_recive_message(result)

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

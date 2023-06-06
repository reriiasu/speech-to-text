import asyncio
import functools
import eel
import queue
import numpy as np

from concurrent.futures import ThreadPoolExecutor
from audio_utils import create_audio_stream
from vad_utils import VadWrapper

class AudioTranscriber:
    def __init__(self, loop):
        self.loop = loop
        self.whisper_model = None
        self.transcribe_settings = None
        self.selected_audio_device_index = None
        self.vad_wrapper = VadWrapper()
        self.silent_chunks = 0
        self.speech_buffer = []
        self.audio_queue = queue.Queue()
        self.transcribing = False
        self.stream = None
        self._running = asyncio.Event()

    async def transcribe_audio(self):
        with ThreadPoolExecutor() as executor:
            while self.transcribing:
                if not self.transcribing:
                    break
                try:
                    # Get audio data from queue with a timeout
                    audio_data_np = await self.loop.run_in_executor(executor, functools.partial(self.audio_queue.get, timeout=5.0))
                
                    # Create a partial function for the model's transcribe method
                    func = functools.partial(self.whisper_model.transcribe, audio=audio_data_np, **self.transcribe_settings)
                    
                    # Run the transcribe method in a thread
                    segments, _ = await self.loop.run_in_executor(executor, func)
                    
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
            self.silent_chunks = 0
            audio_data = np.frombuffer(indataBytes, dtype=np.int16)
            self.speech_buffer.append(audio_data)
        else:
            self.silent_chunks += 1

        if (
            not is_speech
            and self.silent_chunks > self.vad_wrapper.SILENT_CHUNKS_THRESHOLD
        ):
            if len(self.speech_buffer) > 15:
                audio_data_np = np.concatenate(self.speech_buffer)
                self.speech_buffer.clear()
                self.audio_queue.put(audio_data_np)
            else:
                # noise clear
                self.speech_buffer.clear()

    async def start_transcription(self):
        try:
            self.transcribing = True
            self.stream = create_audio_stream(self.selected_audio_device_index, self.process_audio)
            self.stream.start()
            self._running.set()
            asyncio.run_coroutine_threadsafe(self.transcribe_audio(), self.loop)
            eel.on_recive_message("Transcription started.")
            while self._running.is_set():
                await asyncio.sleep(1)
        except Exception as e:
            for arg in e.args:
                eel.on_recive_message(arg)

    async def stop_transcription(self):
        self.transcribing = False
        if self.stream is not None:
            self._running.clear()
            self.stream.stop()
            self.stream.close()
            self.stream = None
            eel.on_recive_message("Transcription stopped.")
        else:
            eel.on_recive_message("No active stream to stop.")        
        
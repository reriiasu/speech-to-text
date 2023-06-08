import asyncio
import eel
import sys
import threading

from faster_whisper import WhisperModel
from .audio_transcriber import AudioTranscriber
from .utils.audio_utils import get_valid_input_devices
from .utils.file_utils import read_json

eel.init('web')

transcriber:AudioTranscriber = None
event_loop: asyncio.AbstractEventLoop = None
thread: threading.Thread = None

@eel.expose
def get_valid_devices():
    devices = get_valid_input_devices()
    return [{'index': d['index'], 'name':  f"{d['name']} {d['host_api_name']} ({d['max_input_channels']} in)" } for d in devices]

@eel.expose
def get_model_sizes():
    return read_json('model_sizes')

@eel.expose
def get_languages():
    return read_json('languages')

@eel.expose
def start_transcription(selected_audio_device_index, model_settings, transcribe_settings):
    global transcriber, event_loop, thread
    try:
        filtered_model_settings = get_filtered_model_settings(model_settings)
        whisper_model = WhisperModel(**filtered_model_settings)
        filtered_transcribe_settings = get_filtered_transcribe_settings(transcribe_settings)
        
        event_loop = asyncio.new_event_loop()
        
        transcriber = AudioTranscriber(event_loop, whisper_model, filtered_transcribe_settings, selected_audio_device_index)
        asyncio.set_event_loop(event_loop)
        thread = threading.Thread(target=event_loop.run_forever, daemon=True)
        thread.start()        
    
        asyncio.run_coroutine_threadsafe(transcriber.start_transcription(), event_loop)
    except Exception as e:
        for arg in e.args:
            eel.on_recive_message(arg)
            
@eel.expose
def stop_transcription():
    global transcriber, event_loop, thread
    if transcriber is None:
        eel.transcription_stoppd()    
        return
    future = asyncio.run_coroutine_threadsafe(transcriber.stop_transcription(), event_loop)
    future.result()

    if thread.is_alive():
        event_loop.call_soon_threadsafe(event_loop.stop)
        thread.join()
    transcriber = None
    event_loop = None
    thread = None    
    
    eel.transcription_stoppd()    

def get_filtered_model_settings(settings):
    valid_keys = WhisperModel.__init__.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}
    
def get_filtered_transcribe_settings(settings):
    valid_keys = WhisperModel.transcribe.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}

def on_close(page, sockets):
    print(page, 'was closed')

    if transcriber and transcriber.transcribing:
        stop_transcription()
    sys.exit()

if __name__ == "__main__":
    eel.start('index.html', size=(1024, 1024), close_callback=on_close) 


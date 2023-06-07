import asyncio
import eel
import sys
import threading
import json

from faster_whisper import WhisperModel
from audio_transcriber import AudioTranscriber
from audio_utils import get_valid_input_devices

eel.init('web')

@eel.expose
def get_valid_devices():
    devices = get_valid_input_devices()
    return [{'index': d['index'], 'name':  f"{d['name']} {d['host_api_name']} ({d['max_input_channels']} in)" } for d in devices]

@eel.expose
def get_model_sizes():
    with open('json\model_sizes.json', 'r') as f:
        model_sizes = json.load(f)['model_sizes']
    return model_sizes

@eel.expose
def get_languages():
    with open('json\languages.json', 'r') as f:
        data = json.load(f)
    return data['languages']

@eel.expose
def start_transcription(selected_audio_device_index, model_settings, transcribe_settings):
    try:
        transcriber.transcribe_settings = get_filtered_transcribe_settings(transcribe_settings)
        filtered_model_settings = get_filtered_model_settings(model_settings)
        transcriber.whisper_model = WhisperModel(**filtered_model_settings)
        transcriber.selected_audio_device_index = selected_audio_device_index
        run_asyncio(transcriber.start_transcription())
    except Exception as e:
        for arg in e.args:
            eel.on_recive_message(arg)
            
@eel.expose
def stop_transcription():
    run_asyncio(transcriber.stop_transcription())
    transcriber.whisper_model = None
    eel.transcription_stoppd()

def run_asyncio(coro):
    asyncio.run_coroutine_threadsafe(coro, loop)

def get_filtered_model_settings(settings):
    valid_keys = WhisperModel.__init__.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}
    
def get_filtered_transcribe_settings(settings):
    valid_keys = WhisperModel.transcribe.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}

def on_close(page, sockets):
    stop_transcription()
    print(page, 'was closed')

    if transcriber.transcribing:
        run_asyncio(transcriber.stop_transcription())

    if t.is_alive():
        loop.call_soon_threadsafe(loop.stop)
        t.join()
    sys.exit()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    transcriber = AudioTranscriber(loop)
    t = threading.Thread(target=loop.run_forever)
    t.setDaemon(True)
    t.start()
    eel.start('index.html', size=(1024, 1024), close_callback=on_close) 


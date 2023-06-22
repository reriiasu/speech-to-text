import asyncio
import eel
import sys
import threading

from faster_whisper import WhisperModel
from .audio_transcriber import AppOptions
from .audio_transcriber import AudioTranscriber
from .utils.audio_utils import get_valid_input_devices
from .utils.file_utils import read_json, write_json

eel.init("web")

transcriber: AudioTranscriber = None
event_loop: asyncio.AbstractEventLoop = None
thread: threading.Thread = None


@eel.expose
def get_valid_devices():
    devices = get_valid_input_devices()
    return [
        {
            "index": d["index"],
            "name": f"{d['name']} {d['host_api_name']} ({d['max_input_channels']} in)",
        }
        for d in devices
    ]


@eel.expose
def get_dropdown_options():
    data_types = ["model_sizes", "compute_types", "languages"]

    dropdown_options = {}
    for data_type in data_types:
        data = read_json("assets", data_type)
        dropdown_options[data_type] = data[data_type]

    return dropdown_options


@eel.expose
def get_user_settings():
    data_types = ["app_settings", "model_settings", "transcribe_settings"]
    userSettings = {}

    try:
        data = read_json("settings", "user_settings")
        for data_type in data_types:
            userSettings[data_type] = data[data_type]
    except Exception as e:
        eel.on_recive_message(str(e))

    return userSettings


@eel.expose
def start_transcription(userSettings):
    global transcriber, event_loop, thread
    try:
        filtered_app_settings = get_filtered_app_settings(userSettings["app_settings"])
        app_settings = AppOptions(**filtered_app_settings)
        filtered_model_settings = get_filtered_model_settings(
            userSettings["model_settings"]
        )
        whisper_model = WhisperModel(**filtered_model_settings)
        filtered_transcribe_settings = get_filtered_transcribe_settings(
            userSettings["transcribe_settings"]
        )
        event_loop = asyncio.new_event_loop()

        transcriber = AudioTranscriber(
            event_loop, whisper_model, filtered_transcribe_settings, app_settings
        )
        asyncio.set_event_loop(event_loop)
        thread = threading.Thread(target=event_loop.run_forever, daemon=True)
        thread.start()

        write_json(
            "settings",
            "user_settings",
            {
                "app_settings": filtered_app_settings,
                "model_settings": filtered_model_settings,
                "transcribe_settings": filtered_transcribe_settings,
            },
        )

        asyncio.run_coroutine_threadsafe(transcriber.start_transcription(), event_loop)
    except Exception as e:
        eel.on_recive_message(str(e))


@eel.expose
def stop_transcription():
    global transcriber, event_loop, thread
    if transcriber is None:
        eel.transcription_stoppd()
        return
    future = asyncio.run_coroutine_threadsafe(
        transcriber.stop_transcription(), event_loop
    )
    future.result()

    if thread.is_alive():
        event_loop.call_soon_threadsafe(event_loop.stop)
        thread.join()
    transcriber = None
    event_loop = None
    thread = None

    eel.transcription_stoppd()


def get_filtered_app_settings(settings):
    valid_keys = AppOptions.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def get_filtered_model_settings(settings):
    valid_keys = WhisperModel.__init__.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def get_filtered_transcribe_settings(settings):
    valid_keys = WhisperModel.transcribe.__annotations__.keys()
    return {k: v for k, v in settings.items() if k in valid_keys}


def on_close(page, sockets):
    print(page, "was closed")

    if transcriber and transcriber.transcribing:
        stop_transcription()
    sys.exit()


if __name__ == "__main__":
    eel.start("index.html", size=(1024, 1024), close_callback=on_close)

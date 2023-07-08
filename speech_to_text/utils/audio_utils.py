import sounddevice as sd
import io
import soundfile as sf
import numpy as np
import librosa


# get a list of valid input devices
def get_valid_input_devices():
    valid_devices = []
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()

    for device in devices:
        if device["max_input_channels"] > 0:
            device["host_api_name"] = hostapis[device["hostapi"]]["name"]
            valid_devices.append(device)
    return valid_devices


# create an audio stream
def create_audio_stream(selected_device, callback):
    RATE = 16000
    CHUNK = 512
    CHANNELS = 1
    DTYPE = "float32"

    stream = sd.InputStream(
        device=selected_device,
        channels=CHANNELS,
        samplerate=RATE,
        callback=callback,
        dtype=DTYPE,
        blocksize=CHUNK,
    )

    return stream


def base64_to_audio(audio_data):
    audio_bytes = bytes(audio_data)
    audio_file = io.BytesIO(audio_bytes)
    data, samplerate = sf.read(audio_file)
    # whisper samplerate is 16k
    resample_data = librosa.resample(y=data, orig_sr=samplerate, target_sr=16000)

    return resample_data.astype(np.float32)

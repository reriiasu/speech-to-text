import pyaudio


# 有効なインプットデバイスリストを取得する関数
def get_valid_input_devices():
    valid_devices = []
    audio = pyaudio.PyAudio()
    device_count = audio.get_device_count()
    default_host_api_info = audio.get_default_host_api_info()
    default_host_api_index = default_host_api_info["index"]

    for i in range(device_count):
        device_info = audio.get_device_info_by_index(i)
        if (
            device_info["maxInputChannels"] > 0
            and device_info["hostApi"] == default_host_api_index
        ):
            valid_devices.append(device_info)

    return valid_devices


# 有効なインプットデバイスリストを表示する関数
def display_valid_input_devices(valid_devices):
    for device_info in valid_devices:
        print(
            f"DeviceIndex: {device_info['index']}, DeviceName: {device_info['name']}, 入力チャンネル数: {device_info['maxInputChannels']}"
        )


# オーディオストリームを作成する関数
def create_audio_stream(selected_device_index, callback):
    RATE = 16000
    CHUNK = 480
    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=selected_device_index,
        frames_per_buffer=CHUNK,
        stream_callback=callback,
    )

    return stream

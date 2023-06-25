import os
import json
import soundfile as sf

script_dir = os.path.dirname(os.path.abspath(__file__))
python_root_dir = os.path.dirname(script_dir)
app_root_dir = os.path.dirname(python_root_dir)


def read_json(dir_name: str, json_name: str):
    file_path = os.path.join(python_root_dir, dir_name, json_name + ".json")
    with open(file_path, "r") as f:
        data = json.load(f)
    return data


def write_json(dir_name: str, json_name: str, data: dict):
    file_path = os.path.join(python_root_dir, dir_name, json_name + ".json")
    with open(file_path, "w") as f:
        json.dump(data, f)


def write_audio(dir_name: str, file_name: str, data):
    file_path = os.path.join(app_root_dir, dir_name, file_name + ".wav")

    # If a file with the same name already exists, remove it to forcefully write
    if os.path.exists(file_path):
        os.remove(file_path)

    sf.write(file_path, data, 16000)

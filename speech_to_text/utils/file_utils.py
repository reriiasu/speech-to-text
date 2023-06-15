import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)


def read_json(dir_name: str, json_name: str):
    file_path = os.path.join(parent_dir, dir_name, json_name + '.json')
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def write_json(dir_name: str, json_name: str, data: dict):
    file_path = os.path.join(parent_dir, dir_name, json_name + '.json')
    with open(file_path, 'w') as f:
        json.dump(data, f)

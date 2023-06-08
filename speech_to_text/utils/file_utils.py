import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

def read_json(jsonName: str):
    file_path = os.path.join(parent_dir, 'assets', jsonName + '.json')
    with open(file_path, 'r') as f:
        model_sizes = json.load(f)[jsonName]
    return model_sizes
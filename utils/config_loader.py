import json

def load_config(config_path='config.json'):
    with open(config_path, 'r') as f:
        return json.load(f)
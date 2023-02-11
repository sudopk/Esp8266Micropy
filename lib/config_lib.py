import json
import os

CONFIG_FILE = '/lib/config.json'

PULSE_MS_KEY = 'pulsems'

DEFAULT_CONFIG = {PULSE_MS_KEY: 50}

def load_config() -> dict:
    print(f'Default config: {DEFAULT_CONFIG}')
    config = dict(DEFAULT_CONFIG)
    if path_exists(CONFIG_FILE):
        print(f'Loading config from file: {CONFIG_FILE}')
        with open(CONFIG_FILE, "r") as c:
            try:
                config.update(json.loads(c.read()))
            except ValueError as e:  # If file has invalid json.
                print(f'Ignoring config load error: {e}')
                pass
    print(f'Config after loading: {config}')
    return config


def save_config(config: dict):
    with open(CONFIG_FILE, "w") as c:
        c.write(json.dumps(config))

def path_exists(path: str) -> bool:
    try:
        os.stat(path)
        return True
    except OSError:
        return False
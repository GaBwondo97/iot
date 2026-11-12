import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent


def load_config(filename):
    file_path = CONFIG_DIR / filename

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {file_path}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in configuration file: {filename}"
        ) from exc


def get_mqtt_config():
    return load_config("mqtt_config.json")


def get_sensor_config():
    return load_config("sensors.json")
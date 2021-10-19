import json
import datetime
from pathlib import Path


def get_project_dir():
    return Path(__file__).resolve().parents[1]


def load_json(path_from_root):
    with open(get_project_dir() / path_from_root) as file:
        items = json.load(file)
    return items


def load_api_keys():
    keys = load_json('config/api_key.json')
    api_key = keys['api_key']
    api_secret = keys['api_secret']
    return api_key, api_secret


def convert_timestamp_to_datetime(t):
    return datetime.datetime.fromtimestamp(int(t) / 1000)

import json
import datetime
from pathlib import Path
from typing import List

import pandas as pd


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


def cast_all_to_float(df: pd.DataFrame, except_columns: List = None):
    if except_columns is None:
        except_columns = []
    for c in set(df.columns) - set(except_columns):
        try:
            df[c] = df[c].astype(float)
            df[c] = df[c].round(10)
        except ValueError:
            pass

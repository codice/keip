import json
from typing import Mapping


def load_json_as_dict(filepath: str) -> Mapping:
    with open(filepath, "r") as f:
        return json.load(f)

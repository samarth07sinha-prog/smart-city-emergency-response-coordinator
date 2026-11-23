"""Load a fresh, editable sample dataset on every call."""

import json
from pathlib import Path


def load_sample_data() -> dict:
    path = Path(__file__).resolve().parent.parent / "data" / "sample_city.json"
    return json.loads(path.read_text(encoding="utf-8"))

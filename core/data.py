"""Load a fresh, editable sample dataset on every call."""

import json
from pathlib import Path


def load_sample_data() -> dict:
    path = Path(__file__).resolve().parent.parent / "data" / "sample_city.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_varanasi_data() -> dict:
    """Load the local Varanasi snapshot. Run python -m core.varanasi to create it."""
    path = Path(__file__).resolve().parent.parent / "data" / "varanasi.local.json"
    return json.loads(path.read_text(encoding="utf-8"))

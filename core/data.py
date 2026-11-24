"""Load a fresh, editable sample dataset on every call."""

import gzip
import json
from pathlib import Path


def load_sample_data() -> dict:
    path = Path(__file__).resolve().parent.parent / "data" / "sample_city.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_varanasi_data() -> dict:
    """Prefer a refreshed local network and fall back to the bundled Varanasi extract."""
    path = Path(__file__).resolve().parent.parent / "data" / "varanasi.local.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    with gzip.open(path.with_name("varanasi.roads.json.gz"), "rt", encoding="utf-8") as src:
        return json.load(src)

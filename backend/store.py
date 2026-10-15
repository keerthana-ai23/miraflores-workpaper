
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

DATA_DIR = Path(os.environ.get("WORKPAPER_DATA", Path(__file__).resolve().parent.parent / "data"))
PACKET_PATH = DATA_DIR / "packet.json"
STATE_PATH = DATA_DIR / "state.json"

_lock = threading.Lock()


class Packet:
    

    def __init__(self, raw: dict):
        self.raw = raw
        self.documents = raw["documents"]
        self.extracted_values = raw["extracted_values"]
        self.doc_by_id = {d["id"]: d for d in self.documents}
        self.ev_by_id = {e["id"]: e for e in self.extracted_values}
        self.versions = {rv["version"]: rv for rv in raw["return_versions"]}
        self.lines_by_version = {
            v: {line["key"]: line for line in rv["lines"]}
            for v, rv in self.versions.items()
        }

    def version(self, v: str) -> dict:
        return self.versions[v]

    def lines(self, v: str) -> list[dict]:
        return self.versions[v]["lines"]

    def line(self, v: str, key: str) -> dict | None:
        return self.lines_by_version[v].get(key)


def load_packet() -> Packet:
    with open(PACKET_PATH, encoding="utf-8") as fh:
        return Packet(json.load(fh))



_DEFAULT_STATE = {"notes": {}, "signoffs": {}, "resolved": {}, "adjustments": []}


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH, encoding="utf-8") as fh:
            state = json.load(fh)
        for key, default in _DEFAULT_STATE.items():
            state.setdefault(key, default)
        return state
    return json.loads(json.dumps(_DEFAULT_STATE))


def save_state(state: dict) -> None:
    with _lock:
        tmp = STATE_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=1)
        tmp.replace(STATE_PATH)


PACKET = load_packet()
STATE = load_state()

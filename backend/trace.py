
from __future__ import annotations

from .store import Packet


def proof_tree(packet: Packet, version: str, key: str, depth: int = 0) -> dict | None:
    line = packet.line(version, key)
    if line is None:
        return None
    node = {
        "key": line["key"],
        "label": line["label"],
        "form": line.get("form"),
        "value": line.get("value"),
        "rule": line.get("rule"),
        "note": line.get("note"),
        "sources": [],
        "inputs": [],
    }
    for sid in line.get("sources") or []:
        ev = packet.ev_by_id.get(sid)
        if ev is None:
            continue
        doc = packet.doc_by_id.get(ev["document_id"], {})
        node["sources"].append({
            "ev_id": ev["id"],
            "document_id": ev["document_id"],
            "document_title": doc.get("title"),
            "page": ev["page"],
            "field": ev["field"],
            "label": ev["label"],
            "value": ev["value"],
            "confidence": ev.get("confidence"),
        })
    if depth < 4:  
        for sub_key in line.get("inputs") or []:
            sub = proof_tree(packet, version, sub_key, depth + 1)
            if sub is not None:
                node["inputs"].append(sub)
    return node


def used_value_ids(packet: Packet, version: str) -> set[str]:
    used: set[str] = set()
    for line in packet.lines(version):
        used.update(line.get("sources") or [])
    return used

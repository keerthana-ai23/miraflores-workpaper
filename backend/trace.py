"""Proof trees: expand any return line down to its source documents.

Every number in the workpaper is a claim with a receipt. A line either
*traces* to extracted values (document, page, field, confidence) or is
*computed* from other lines via a named rule. This module expands both,
recursively, so a reviewer can audit any figure in one click — and so the
"unused evidence" report can show which extracted values the return never
relied on (a completeness question in its own right).
"""
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
    if depth < 4:  # the packet's rule graph is shallow; cap defensively
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

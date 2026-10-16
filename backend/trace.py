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
    node["equation"] = _equation(node)
    return node


def _fmt(n: float) -> str:
    return f"{n:,.2f}".rstrip("0").rstrip(".")


def _equation(node: dict) -> str | None:
    """Render a readable calculation when the inputs' arithmetic is plain.

    The packet names the rule but not its operators, so an equation is only
    shown when it can be *verified* against the numbers themselves: if the
    inputs sum to the value, show the addition; if the first input minus the
    rest matches, show the subtraction. Otherwise no equation is claimed —
    the inputs are simply listed. Showing only verified arithmetic is the
    same honesty rule as the rest of the workpaper.
    """
    vals = [sub["value"] for sub in node["inputs"]]
    target = node["value"]
    if len(vals) < 2 or not all(isinstance(v, (int, float)) for v in vals):
        return None
    if not isinstance(target, (int, float)):
        return None
    if abs(sum(vals) - target) < 0.01:
        return " + ".join(_fmt(v) for v in vals) + f" = {_fmt(target)}"
    if abs(vals[0] - sum(vals[1:]) - target) < 0.01:
        return _fmt(vals[0]) + "".join(f" - {_fmt(v)}" for v in vals[1:]) + f" = {_fmt(target)}"
    return None


def used_value_ids(packet: Packet, version: str) -> set[str]:
    used: set[str] = set()
    for line in packet.lines(version):
        used.update(line.get("sources") or [])
    return used

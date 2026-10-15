
from __future__ import annotations

import re

from .store import Packet

SEVERITIES = ("blocker", "question", "info")


def scope_of(line: dict) -> str:
    
    form = line.get("form", "")
    if form.startswith(("F8949", "SchD")):
        return "Capital gains"
    if form.startswith("SchCA") or "540" in form:
        return "California"
    if form.startswith(("SchC", "F4562-C")):
        return "Business (Sch C)"
    if form.startswith("SchE"):
        return "Rentals"
    if form.startswith("SchB"):
        return "Interest & dividends"
    if form.startswith(("F1040", "Sch1", "Sch2", "Sch3")):
        return "Wages & main form"
    if form.startswith("SchA"):
        return "Deductions (Sch A)"
    if "7203" in form or form.startswith("SchK"):
        return "S-corp & K-1s"
    if form.startswith(("F8606", "F8889", "F5498")):
        return "Retirement & HSA"
    return "Other"


def run_checks(packet: Packet, version: str) -> list[dict]:
    rv = packet.version(version)
    lines = packet.lines(version)
    checks: list[dict] = []

   
    for line in lines:
        if line.get("form") == "F8949" and re.search(r"basis 0\.00", line.get("label", "")):
            if isinstance(line.get("value"), (int, float)) and line["value"] > 0:
                src = next(
                    (packet.ev_by_id[s] for s in line.get("sources", []) if s in packet.ev_by_id),
                    None,
                )
                checks.append({
                    "id": f"zero-basis:{line['key']}",
                    "severity": "blocker",
                    "scope": scope_of(line),
                    "title": f"Zero basis used — {line['label'].split(';')[0]}",
                    "detail": (
                        f"Proceeds of {line['value']:,.2f} are taxed as pure gain because the "
                        f"source document reports no basis"
                        + (f" ({src['document_id']})." if src else ".")
                        + " If the asset was already taxed another way (e.g. RSU vesting "
                          "already in wages) the income is double-counted. Supply the real "
                          "basis or a supplemental statement before filing."
                    ),
                    "refs": [line["key"], *(line.get("sources") or [])],
                })

   
    for doc in packet.documents:
        extraction = doc.get("extraction") or {}
        if extraction.get("status") == "partial":
            checks.append({
                "id": f"partial-extraction:{doc['id']}",
                "severity": "blocker",
                "scope": "Documents",
                "title": f"Document only partially read — {doc['id']} {doc['title']}",
                "detail": (
                    (extraction.get("reason") or "Some pages were not extracted.")
                    + " Anything on the unread pages is missing from the return."
                ),
                "refs": [doc["id"]],
            })

    
    used: set[str] = set()
    for line in lines:
        used.update(line.get("sources") or [])
    for ev in packet.extracted_values:
        if ev["id"] in used and (ev.get("confidence") or 1) < 0.9:
            checks.append({
                "id": f"low-confidence:{ev['id']}",
                "severity": "question",
                "scope": "Documents",
                "title": (
                    f"Low-confidence read used in the return — {ev['document_id']} "
                    f"{ev['field']} = {ev['value']} (confidence {ev['confidence']})"
                ),
                "detail": f"{ev['label']}. Confirm against the document before filing.",
                "refs": [ev["id"], ev["document_id"]],
            })

  
    for i, diag in enumerate(rv.get("diagnostics") or []):
        checks.append({
            "id": f"engine-diagnostic:{version}:{i}",
            "severity": "question" if diag.get("severity") == "warning" else "info",
            "scope": "Engine diagnostics",
            "title": diag.get("code", "Diagnostic"),
            "detail": diag.get("message", ""),
            "refs": diag.get("refs") or [],
        })

   
    for doc in packet.documents:
        if re.search(r"CORRECTED", doc.get("title", ""), re.I):
            checks.append({
                "id": f"corrected-document:{doc['id']}",
                "severity": "info",
                "scope": "Documents",
                "title": f"Corrected document in file — {doc['id']} {doc['title']}",
                "detail": (
                    "This document supersedes an earlier version. Figures traced from it "
                    "show which version they came from; earlier versions of the return "
                    "may still use the superseded values."
                ),
                "refs": [doc["id"]],
            })

    return checks


def scope_hash(packet: Packet, version: str, scope: str, adjustments: list[dict]) -> int:
    
    rv_lines = packet.lines(version)
    blob = ";".join(
        f"{l['key']}={l['value']}" for l in rv_lines if scope_of(l) == scope
    )
    blob += "|" + ";".join(
        f"{a['line_key']}:{a['delta']}"
        for a in adjustments
        if scope_of(packet.line(version, a["line_key"]) or {"form": ""}) == scope
    )
    h = 0
    for ch in blob:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h

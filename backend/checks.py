"""Validation engine — checks that don't trust the pipeline or the engine.

Each check reconciles two independent parts of the packet against each other
(source documents vs. extracted values vs. the computed return) and emits an
*open item* when they disagree. An open item is the workpaper's unit of work:
it has a severity, an owner scope, and it blocks sign-off for its area until
a human resolves or explicitly accepts it.

Design rule that motivates most of these checks: **unknown is a first-class
state**. A value the source document did not report must surface as missing,
never silently become zero — zero is a claim, and a false one.
"""
from __future__ import annotations

import re

from .store import Packet

SEVERITIES = ("blocker", "question", "info")


def scope_of(line: dict) -> str:
    """Map a return line to the review area (scope) it belongs to."""
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

    # 1 — Lots taxed on a zero basis. The label of an 8949 lot line carries the
    # basis the engine used; basis 0.00 on a positive-proceeds lot usually
    # means "not reported" upstream, which must not silently become "zero".
    # Two exclusions keep this check honest:
    #  * aggregate ".total" lines repeat their lots' figures — flagging them
    #    too would count one error two or three times;
    #  * distributions in excess of stock basis are taxed on a zero basis by
    #    law, so they are a verification question, not an error.
    for line in lines:
        if line.get("form") == "F8949" and re.search(r"basis 0\.00", line.get("label", "")):
            if line["key"].endswith(".total"):
                continue
            if isinstance(line.get("value"), (int, float)) and line["value"] > 0:
                if re.search(r"excess of (stock )?basis", line.get("label", ""), re.I):
                    checks.append({
                        "id": f"verify-scorp-basis:{line['key']}",
                        "severity": "question",
                        "scope": scope_of(line),
                        "title": f"Verify S-corp basis — {line['label'].split(';')[0]}",
                        "detail": (
                            "Distributions in excess of stock basis are correctly taxed "
                            "with zero basis, but only if the underlying basis computation "
                            "is right. The basis history (including any prior-year K-1 gap) "
                            "must be verified before this is accepted."
                        ),
                        "refs": [line["key"], *(line.get("sources") or [])],
                    })
                    continue
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

    # 2 — Documents the pipeline only partially read. Unread pages mean
    # transactions that are absent from the return entirely.
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

    # 3 — Low-confidence extracted values that actually feed this version of
    # the return. A shaky read that nothing uses is trivia; one that moves a
    # number is a question a human must answer (it becomes evidence).
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

    # 4 — The engine's own diagnostics, surfaced rather than buried.
    for i, diag in enumerate(rv.get("diagnostics") or []):
        checks.append({
            "id": f"engine-diagnostic:{version}:{i}",
            "severity": "question" if diag.get("severity") == "warning" else "info",
            "scope": "Engine diagnostics",
            "title": diag.get("code", "Diagnostic"),
            "detail": diag.get("message", ""),
            "refs": diag.get("refs") or [],
        })

    # 5 — Corrected documents: make the supersession chain visible so nobody
    # traces a figure to a version that was later replaced.
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
    """Content hash of everything a sign-off covers.

    A sign-off is bound to the exact data it approved: if any line value in
    the scope changes, or an adjustment is recorded against it, the hash
    changes and the sign-off reopens itself.
    """
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

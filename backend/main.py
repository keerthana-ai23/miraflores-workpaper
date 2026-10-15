"""Workpaper API — FastAPI service over the MiraFlores packet.

Run:  uvicorn backend.main:app --reload --port 8000
Then open http://localhost:8000 (the frontend is served by this app).

The API mirrors the workpaper's mental model:
  /api/summary            return totals per version (from the engine)
  /api/proof-status       per-area status: blockers, sign-offs, staleness
  /api/lines              return lines (totals-first grouping is a client concern;
                          `form` and `q` filters keep payloads small)
  /api/lines/{key}/trace  the proof tree for one line
  /api/documents          the document index with extraction coverage
  /api/documents/{id}     one document: simulated pages + extracted values
  /api/checks             open items from the validation engine
  /api/notes, /api/signoffs, /api/adjustments, /api/resolve
                          the human-in-the-loop layer (persisted)
  /api/ask                retrieval-augmented assistant (see assistant.py)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import assistant, checks as checks_mod, trace as trace_mod
from .store import PACKET, STATE, save_state

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="MiraFlores Workpaper", version="1.0.0")


# ------------------------------------------------------------------ schemas
class NoteIn(BaseModel):
    scope_id: str
    text: str
    role: str = "Preparer"


class SignoffIn(BaseModel):
    scope: str
    role: str
    version: str = "v3"


class ResolveIn(BaseModel):
    check_id: str
    resolved: bool = True


class AdjustmentIn(BaseModel):
    line_key: str
    delta: float
    why: str
    role: str = "Preparer"
    version: str = "v3"


class AskIn(BaseModel):
    question: str
    version: str = "v3"


# ------------------------------------------------------------------ helpers
def _version_or_404(version: str) -> str:
    if version not in PACKET.versions:
        raise HTTPException(404, f"unknown return version {version}")
    return version


# -------------------------------------------------------------------- reads
@app.get("/api/meta")
def meta():
    return {
        "packet": PACKET.raw.get("packet"),
        "versions": list(PACKET.versions.keys()),
        "document_count": len(PACKET.documents),
        "value_count": len(PACKET.extracted_values),
    }


@app.get("/api/summary")
def summary(version: str = "v3"):
    _version_or_404(version)
    return PACKET.version(version).get("summary")


@app.get("/api/proof-status")
def proof_status(version: str = "v3"):
    _version_or_404(version)
    open_items = checks_mod.run_checks(PACKET, version)
    resolved = STATE["resolved"]
    scopes = sorted({checks_mod.scope_of(l) for l in PACKET.lines(version)})
    areas = []
    for scope in scopes:
        mine = [c for c in open_items if c["scope"] == scope and not resolved.get(c["id"])]
        signoff = STATE["signoffs"].get(f"{version}:{scope}")
        stale = bool(
            signoff
            and signoff["hash"] != checks_mod.scope_hash(PACKET, version, scope, STATE["adjustments"])
        )
        areas.append({
            "scope": scope,
            "open_items": len(mine),
            "blockers": sum(1 for c in mine if c["severity"] == "blocker"),
            "line_count": sum(1 for l in PACKET.lines(version) if checks_mod.scope_of(l) == scope),
            "signoff": signoff,
            "signoff_stale": stale,
        })
    return {"version": version, "areas": areas}


@app.get("/api/lines")
def lines(version: str = "v3", form: str | None = None, q: str | None = None):
    _version_or_404(version)
    out = PACKET.lines(version)
    if form:
        out = [l for l in out if l.get("form") == form]
    if q:
        needle = q.lower()
        out = [l for l in out if needle in (l["key"] + " " + l["label"]).lower()]
    return {"version": version, "count": len(out), "lines": out}


@app.get("/api/forms")
def forms(version: str = "v3"):
    _version_or_404(version)
    counts: dict[str, int] = {}
    for line in PACKET.lines(version):
        counts[line.get("form", "")] = counts.get(line.get("form", ""), 0) + 1
    return {"version": version, "forms": counts}


@app.get("/api/lines/{key}/trace")
def line_trace(key: str, version: str = "v3"):
    _version_or_404(version)
    tree = trace_mod.proof_tree(PACKET, version, key)
    if tree is None:
        raise HTTPException(404, f"no line {key} in {version}")
    return tree


@app.get("/api/documents")
def documents():
    out = []
    for doc in PACKET.documents:
        out.append({
            "id": doc["id"],
            "title": doc["title"],
            "document_type": doc.get("document_type"),
            "issuer": doc.get("issuer"),
            "belongs_to": doc.get("belongs_to"),
            "received_at": doc.get("received_at"),
            "page_count": doc.get("page_count"),
            "extraction": doc.get("extraction"),
            "value_count": sum(1 for e in PACKET.extracted_values if e["document_id"] == doc["id"]),
        })
    return {"documents": out}


@app.get("/api/documents/{doc_id}")
def document(doc_id: str):
    doc = PACKET.doc_by_id.get(doc_id)
    if doc is None:
        raise HTTPException(404, f"no document {doc_id}")
    values = [e for e in PACKET.extracted_values if e["document_id"] == doc_id]
    return {**doc, "extracted_values": values}


@app.get("/api/checks")
def checks(version: str = "v3", include_resolved: bool = False):
    _version_or_404(version)
    out = checks_mod.run_checks(PACKET, version)
    for chk in out:
        chk["resolved"] = bool(STATE["resolved"].get(chk["id"]))
        chk["notes"] = STATE["notes"].get(chk["id"], [])
    if not include_resolved:
        out = [c for c in out if not c["resolved"]]
    return {"version": version, "checks": out}


@app.get("/api/state")
def state():
    return STATE


# ------------------------------------------------------------------- writes
@app.post("/api/notes")
def add_note(body: NoteIn):
    entry = {"role": body.role, "text": body.text, "ts": datetime.now().isoformat(timespec="seconds")}
    STATE["notes"].setdefault(body.scope_id, []).append(entry)
    save_state(STATE)
    return entry


@app.post("/api/signoffs")
def sign_off(body: SignoffIn):
    _version_or_404(body.version)
    record = {
        "role": body.role,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "hash": checks_mod.scope_hash(PACKET, body.version, body.scope, STATE["adjustments"]),
    }
    STATE["signoffs"][f"{body.version}:{body.scope}"] = record
    save_state(STATE)
    return record


@app.post("/api/resolve")
def resolve(body: ResolveIn):
    STATE["resolved"][body.check_id] = body.resolved
    save_state(STATE)
    return {"check_id": body.check_id, "resolved": body.resolved}


@app.post("/api/adjustments")
def add_adjustment(body: AdjustmentIn):
    _version_or_404(body.version)
    if PACKET.line(body.version, body.line_key) is None:
        raise HTTPException(404, f"no line {body.line_key} in {body.version}")
    rates = PACKET.version(body.version).get("tax_effect_rates") or {}
    entry = {
        "line_key": body.line_key,
        "delta": body.delta,
        "why": body.why,
        "role": body.role,
        "version": body.version,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "rates_available": sorted(rates.keys()),
    }
    STATE["adjustments"].append(entry)
    save_state(STATE)
    return entry


@app.post("/api/ask")
def ask(body: AskIn):
    _version_or_404(body.version)
    return assistant.answer(PACKET, body.version, body.question)


# ----------------------------------------------------------------- frontend
@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


from __future__ import annotations

import json
import os
import re
import urllib.request

from .checks import run_checks
from .store import Packet

STOP = set("what is the a an of to in for and or does did do how much many was were are this that with from".split())
TOKEN = re.compile(r"[a-z0-9$.,-]+")


def _tokens(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP and len(t) > 1]


def build_chunks(packet: Packet, version: str) -> list[dict]:
    chunks: list[dict] = []
    for doc in packet.documents:
        for page in doc.get("pages", []):
            chunks.append({
                "kind": "document",
                "ref": f"{doc['id']} p{page['page']}",
                "title": doc["title"],
                "text": page.get("printed_content", ""),
            })
    for line in packet.lines(version):
        chunks.append({
            "kind": "return_line",
            "ref": line["key"],
            "title": line.get("form", ""),
            "text": f"{line['label']} = {line.get('value')}",
        })
    for chk in run_checks(packet, version):
        chunks.append({
            "kind": "open_item",
            "ref": chk["id"],
            "title": chk["title"],
            "text": chk["detail"],
        })
    return chunks


def retrieve(packet: Packet, version: str, question: str, k: int = 5) -> list[dict]:
    q = set(_tokens(question))
    if not q:
        return []
    scored = []
    for chunk in build_chunks(packet, version):
        text_tokens = _tokens(chunk["title"] + " " + chunk["text"])
        score = sum(1 for t in text_tokens if t in q)
        # Numbers and ids in the question are strong signals; weight them.
        score += 3 * sum(1 for t in q if any(ch.isdigit() for ch in t) and t in text_tokens)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda pair: -pair[0])
    return [chunk for _, chunk in scored[:k]]


def _llm_answer(question: str, evidence: list[dict]) -> str | None:
    """Call an OpenAI chat model with the retrieved evidence. Returns None
    when no key is configured or the call fails, so the caller can fall back
    to the extractive answer instead of failing the request."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    context = "\n\n".join(f"[{c['ref']}] {c['title']}: {c['text']}" for c in evidence)
    payload = {
        "model": os.environ.get("WORKPAPER_LLM_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You answer questions about one household's 2025 tax workpaper. "
                    "Use ONLY the evidence provided. Cite every claim with its bracketed "
                    "reference (e.g. [D28 p1] or [F8949.B.N1]). If the evidence does not "
                    "answer the question, say so plainly. Be brief."
                ),
            },
            {"role": "user", "content": f"Evidence:\n{context}\n\nQuestion: {question}"},
        ],
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        return body["choices"][0]["message"]["content"]
    except Exception:
        return None


def answer(packet: Packet, version: str, question: str) -> dict:
    evidence = retrieve(packet, version, question)
    if not evidence:
        return {
            "answer": "I couldn't find anything in the packet that answers that. "
                      "Try naming a document, a form line, or a topic (e.g. 'RSU basis').",
            "citations": [],
            "mode": "none",
        }
    llm = _llm_answer(question, evidence)
    if llm:
        return {"answer": llm, "citations": [c["ref"] for c in evidence], "mode": "llm"}
    extractive = "Here's what the packet says:\n" + "\n".join(
        f"• [{c['ref']}] {c['text'][:280]}" for c in evidence
    )
    return {"answer": extractive, "citations": [c["ref"] for c in evidence], "mode": "extractive"}

# Oct 16 MiraFlores session — start kit
Say "start" in chat and we go in this order. Total ~3 hours, splittable
after step 2. Everything below is checked against the actual repo files
on 2026-10-15.

## Step 1 — Render deploy (~15 min) — DONE 2026-10-15
Live link: https://miraflores-workpaper-3wzv.onrender.com/ (verified
loading from outside). Skip to Step 2 when the session starts.
- render.com → sign in with GitHub → New → Web Service → connect
  `miraflores-workpaper` → Dockerfile auto-detected → Free tier → Create.
- Free tier sleeps: open the live link yourself once before sending
  (first click can take ~1 min), and reviewer-saved state resets on
  restart — known, accepted tradeoff, say it in the video if asked.
- Paste the link into SUBMISSION.md step 2 (GitHub link is already in).

## Step 2 — Learn the code, one file at a time (~1.5 hrs)
Only 5 real files. One plain sentence each:
- `backend/main.py` — the FastAPI API: serves the frontend and the
  endpoints (/api/summary, /api/proof-status, /api/lines + trace,
  /api/documents, /api/checks, /api/notes/signoffs, /api/ask).
- `backend/store.py` — loads data/packet.json once, indexes it, and owns
  the human layer the packet doesn't contain (notes, sign-offs,
  resolutions, adjustments), persisted to a JSON state file.
- `backend/checks.py` — the validation engine: reconciles source
  documents vs extracted values vs the computed return and emits open
  items (blocker/question/info) that block sign-off. Core rule: unknown
  is a first-class state — "not reported" is missing, never silently $0.
- `backend/trace.py` — proof trees: expands any return line down to its
  source documents/pages/fields, or to the named rule that computed it.
- `backend/assistant.py` — the RAG "Ask the workpaper" assistant: chunks
  the packet, scores chunks by term overlap, answers only from the
  packet with citations; LLM used only if OPENAI_API_KEY is set,
  otherwise an extractive cited answer. FAISS is the named upgrade seam.
- Plus `frontend/index.html` — the single page the API serves.
Supporting files: data/packet.json, tests/test_checks.py, Dockerfile,
README.md, DESIGN.md (deliverable 2), FINDINGS.md (deliverable 3).

## Step 3 — Video practice (~45 min), script = VIDEO-SCRIPT-NEW.md
Do NOT use the old video-script.md in miraflores-case-study — it describes
the first draft. Practice questions Keee will ask as Camila's reviewer:
1. Why is "unknown is never $0" the core rule? (Answer: RSU lots taxed on
   zero basis — about $53,020 of gain counted twice — see FINDINGS.md.)
2. Why lexical retrieval instead of embeddings/FAISS?
3. What resets on the Render free tier, and why is that acceptable here?
4. Which errors did the design surface that a spreadsheet would hide?
   (Crypto lot with unknown basis; corrected 1099 page never extracted;
   low-confidence handwritten receipt routed to a human.)

## Step 4 — Record + send (~30 min)
- Record 5–7 min from VIDEO-SCRIPT-NEW.md; upload (Loom/Drive/YouTube
  unlisted — check the link is not private-only).
- Fill the two links in SUBMISSION.md and send its draft email to Camila.

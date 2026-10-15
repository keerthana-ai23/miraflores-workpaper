# Workpaper — MiraFlores AI case study

A web-native tax workpaper for one complex household (the Okafor-Lindqvist
2025 return), built for the MiraFlores AI *AI Engineer (Tax)* case study.

**Core idea: every number is a claim with a receipt.** The atomic unit is not
the form or the document — it is the assertion: one number, the exact place it
came from, how it was verified, and everything that has happened to it since.
Documents and forms are two views over the same assertions.

## Run it

```bash
pip install -r requirements.txt
uvicorn backend.main:app --port 8000
# open http://localhost:8000
```

Or with Docker: `docker build -t workpaper . && docker run -p 8000:8000 workpaper`

Optional: set `OPENAI_API_KEY` to let the "Ask the workpaper" assistant draft
answers with an LLM from retrieved packet evidence. Without a key it returns
the cited evidence itself — it never invents an answer.

Tests: `python -m pytest tests/ -q`

## What it does

- **Proof status (home):** per-area status — what's proven, what's open, what
  blocks filing — plus role-bound sign-offs. A sign-off is bound to a hash of
  the data it approved; change anything underneath and it reopens itself.
- **Return explorer:** all 627 lines across the three computed versions,
  totals-first by form so hundreds of detail lines (every stock sale) don't
  swamp the review. Click any line for its **proof tree**: the exact document,
  page and field it came from, or the rule and input lines that computed it.
- **Documents:** all 74 source documents with extraction-coverage badges and
  simulated renderings built from the packet's printed content, each extracted
  value highlighted (real scans can replace these — every value already
  points at document/page/position).
- **Open items:** a validation engine (`backend/checks.py`) reconciles the
  packet against itself — source documents vs. extracted values vs. the
  computed return — and raises questions instead of burying discrepancies.
  Notes, resolutions, adjustments and sign-offs persist server-side.
- **Ask the workpaper:** retrieval-augmented Q&A over the packet; every answer
  carries citations a reviewer can verify in one click.

## Errors the checks surface in this packet

1. **RSU double taxation (~$53,020).** Three Corvane RSU lots on the Northlake
   1099-B say "basis (not reported)"; the pipeline recorded basis 0 and the
   engine taxed the full proceeds as gain — but RSU value is already taxed as
   wages at vesting. Design rule: *not reported* becomes **missing** (a
   blocker), never zero.
2. **Crypto lot C6** transferred in with no known basis; the engine used $0,
   so the full $5,325 proceeds show as gain. Same rule: unknown basis is a
   first-class open item with a client question attached.
3. **Corrected Meridian 1099 (D31) was only partially extracted** — page 32
   ("Additional transactions") was never read, so those transactions are
   absent from the return. Coverage is tracked per document; a partial read
   blocks its area.
4. **Ambiguous handwritten donation receipt** read at 0.41 confidence
   ($1,500 vs $7,500) and used in the return — routed to a human question.
5. Version traps handled visibly: the corrected 1099 changed four values
   (one flipped a sale from short- to long-term); superseded documents stay
   linked to their replacements.

Checked-and-correct false alarms (documented in the tests' spirit): dividend
lines correctly use box 1a only (1b is a subset); several "half" totals are
the same amount corroborated by two documents, counted once; the backdoor
Roth computes to $26 taxable.

## Architecture

```
backend/
  main.py       FastAPI app — REST API + serves the frontend
  store.py      packet loading/indexing + persisted human state (JSON)
  checks.py     validation engine: reconciliation checks -> open items
  trace.py      proof-tree expansion for any return line
  assistant.py  retrieval + optional LLM drafting, always cited
frontend/
  index.html    single-page UI (no build step)
data/
  packet.json   the delivered packet (74 documents, 3,012 values, 3 versions)
tests/
  test_checks.py  the findings above, as executable expectations
```

Stack choices map to the role: Python + FastAPI (APIs), a document-intelligence
validation pipeline (extraction coverage, confidence, classification by form),
RAG with citations for the assistant, human-in-the-loop review/approval with
full auditability, and a Docker deployment.

## How AI tools were used

AI assistance was used to explore the packet and run the reconciliation
checks that found the errors, and to scaffold the application. The design,
the checks' logic, and every judgment about what counts as an error were
verified against the source documents by hand.

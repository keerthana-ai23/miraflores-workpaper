# Lesson 2 — The code files, in simple words
Same style as Lesson 1: basics first, every word explained, in a flow.
Checked line-by-line against the actual repo files on 2026-10-15.
Order to open them: store.py → checks.py → trace.py → assistant.py → main.py
(main.py last on purpose — it is only the waiter that ties the others together.)

The one idea to hold in your head for all five files:
**The packet is the family's facts. It never changes. Everything a human
does — notes, sign-offs, fixes — lives in a separate layer on top of it.**
Each file below is just one job in that sentence.

---

## FILE 1 — backend/store.py — "the librarian"

**Its one job:** Load the family's file once, make it fast to search,
and keep the humans' layer safe.

Plain walk-through:
- The family's data is one big file, `data/packet.json`: 74 documents,
  the values the computer read from them (3,012 values), and the tax
  return as it was calculated at 3 different moments (called **versions**
  — v1, v2, v3 — like drafts 1, 2, 3 of the same return).
- When the app starts, this file loads that packet **once** and builds
  **indexes**. An index is exactly like the index at the back of a book:
  instead of reading the whole packet to find document D31, the code can
  jump straight to it. It builds four indexes: documents by their ID,
  extracted values by their ID, return versions by name, and return
  lines by version + key.
- The packet itself is **read-only** — this file never lets anything
  change a family fact. That is deliberate: the packet is evidence.
- Everything the *humans* add lives separately, in `data/state.json`:
  **notes** (comments), **sign-offs** (approvals), **resolved** (open
  problems a human closed), and **adjustments** (corrections a human
  recorded). Four boxes, nothing else.
- Every time a human does something, `save_state` writes the whole
  human layer to disk, so nothing is lost if the app restarts. Two
  safety details, in plain words:
  - A **lock** means only one write happens at a time — two reviewers
    saving at the same second cannot corrupt the file.
  - It writes to a temporary file first, then swaps it in — if the
    computer died mid-save, you lose the new save, never the old one.

**Example to say out loud:** "store.py is the librarian. The book —
the packet — is never written in. Reviewers write on sticky notes,
and the librarian keeps those sticky notes in a separate folder and
files them safely every time."

**If Camila asks "why separate the human layer from the packet?"**
Because then you can always prove what the pipeline actually said
versus what a human later decided. Mixing them would destroy the
receipt — the whole point of the app.

---

## FILE 2 — backend/checks.py — "the checker" (the heart of the app)

**Its one job:** Compare the packet against *itself* and turn every
disagreement into a problem card (called an **open item**) for a human.

First, one helper — `scope_of`: every return line is sorted into a
review **area** (called a **scope**) by which tax form it came from.
Example: lines from Form 8949 / Schedule D → "Capital gains";
Schedule CA / Form 540 → "California"; Schedule C → "Business".
This is why the home page can say "8 blockers, all in Capital Gains" —
each check knows which area it belongs to, and an area cannot be
signed off while it still has an open blocker.

Then `run_checks` runs exactly **5 checks**. Each one, plainly:

1. **Zero-basis check (blocker).** It looks at every stock-sale line
   whose label says "basis 0.00" while the sale brought in real money.
   Basis = what the asset cost. A basis of $0 on a real sale almost
   always means the document said "not reported" and the pipeline
   silently turned "we don't know" into zero. This is the RSU error:
   shares already taxed as salary, taxed again in full — about
   $53,020 of gain counted twice. This check is the code form of the
   core rule: **unknown is never $0 — missing is its own state.**
2. **Partially-read document check (blocker).** If a document's
   extraction status is "partial" — some pages never read — anything
   on those pages is missing from the return entirely. Example:
   corrected 1099, document D31, page 32 never extracted.
3. **Low-confidence check (question).** If a value was read with
   confidence below 0.9 **and that value is actually used in the
   return**, a human must confirm it. Example: the handwritten receipt
   read at 0.41. Note the "and used" part — a shaky read that nothing
   uses is trivia; a shaky read that moves a number is a question.
4. **Engine diagnostics check.** The original program already knew
   some of its own warnings — this check lifts them out of the logs
   and shows them as open items instead of burying them.
5. **Corrected-document check (info).** If a document is a CORRECTED
   version, that is flagged so nobody traces a number to an old
   version that was later replaced.

Severity words, plainly: **blocker** = stops sign-off, must be fixed.
**question** = a human must look and decide. **info** = worth knowing,
does not stop anything.

Last piece — `scope_hash`. A **hash** is a fingerprint of data (Lesson 1).
When a reviewer signs off an area, this code makes a fingerprint of
*every line value in that area, plus any human adjustments to it*,
and stores the fingerprint with the signature. Later, the app makes
the fingerprint again. If even one number changed, the fingerprints
differ and the sign-off shows as **stale** — it reopens itself.
Simple words: "the signature is glued to the exact numbers it saw."

**If Camila asks "why not just trust the pipeline's own checks?"**
Because these checks compare *independent parts* of the packet
against each other — documents vs. extracted values vs. the computed
return. The pipeline checking itself would just repeat its own mistake.

---

## FILE 3 — backend/trace.py — "show me the receipt"

**Its one job:** When you click any number, unfold *where it came
from*, step by step, until you land on a document and a page.

Plain walk-through:
- Every return line is one of two kinds. Either it **traces** to
  extracted values — a document, a page, a field, and how confident
  the read was — or it was **computed** from other lines by a named
  rule (for example, a total = these three lines added).
- `proof_tree` handles both, **recursively**. Recursion, plainly:
  the same unfolding step applied again to each smaller piece, like
  opening a folder inside a folder inside a folder, until every
  branch ends at a real document page. It stops at depth 4 — the
  packet's chains are short, and the cap is a safety rail so a loop
  in the data could never make it unfold forever.
- It also powers the opposite question: `used_value_ids` lists every
  extracted value the return actually relied on. Anything extracted
  but never used is a completeness question in its own right —
  "we read this, why did it go nowhere?"

**Example to say:** "Click the $4,220 federal amount. The proof tree
walks it down — total → its parts → each part's document, page and
field. No number in this app is allowed to just sit there unexplained."

---

## FILE 4 — backend/assistant.py — "Ask the workpaper" (the RAG file)

**Its one job:** Answer a reviewer's question using *only this
family's packet*, and show the sources for every answer.

The flow is RAG from Lesson 1, in three real steps in the code:

1. **Chunking.** The packet is cut into small labelled pieces —
   called **chunks**: each document page, each return line, and each
   open item from checks.py. Each chunk carries its own label
   (like "D28 p1" or a return-line key) — that label becomes the
   citation later.
2. **Retrieval.** The question is broken into words; common filler
   words ("what", "is", "the"…) are thrown away; each chunk scores
   points for each question-word it contains. Words with numbers or
   IDs in them score **triple** — a document ID or a dollar amount is
   a much stronger clue than an ordinary word. The top 5 chunks win.
   This plain word-matching method is called **lexical retrieval**.
3. **Generation — with a safety fallback.** *If* an OpenAI key is set
   up, those top 5 chunks are handed to the AI model with a hard
   instruction: "answer ONLY from this evidence, cite every claim,
   and if the evidence does not answer it, say so plainly." The model
   runs at a low **temperature** (0.1) — temperature is a creativity
   dial; low means "stick to the facts, do not improvise."
   *If there is no key, or the call fails*, the app does NOT invent
   an answer and does NOT crash — it returns the evidence itself as
   bullet points with citations. That mode is called **extractive**:
   it extracts the receipts instead of generating prose.

**If Camila asks "why lexical retrieval, not embeddings / FAISS?"**
Honest answer, and it is the designed answer: the packet is small
and fully in memory, so word overlap already finds the right pages,
and there is nothing extra to host or pay for. The retrieval function
is one clean seam — when a corpus outgrows this, a vector index like
FAISS drops into exactly that spot without changing anything else.
**Embeddings / FAISS, plainly:** a way of searching by *meaning*
instead of exact words, using lists of numbers that represent text —
better for very large collections, unnecessary machinery here.

**If Camila asks "can the chat hallucinate?"** (hallucination =
the AI confidently inventing something): It is fenced three ways —
it only ever sees the retrieved chunks, it must cite them, and with
no key it cannot generate at all, it can only quote evidence.

---

## FILE 5 — backend/main.py — "the waiter" (FastAPI)

**Its one job:** Be the doorway. The web page never touches the
files above directly — it asks main.py through the **API**, and
main.py asks the right file and carries the answer back. (Restaurant
from Lesson 1: main.py is the waiter, the other files are the kitchen.)

What it actually does:
- **Reading doors (GET):** the home numbers (`/api/summary`), the
  per-area proof status (`/api/proof-status` — for each area: how
  many open items, how many blockers, whether it is signed off, and
  whether that sign-off has gone stale by re-checking the hash from
  checks.py), the return lines with search filters, one line's proof
  tree (it calls trace.py), the document list with extraction
  coverage, and the open items (it calls checks.py).
- **Writing doors (POST):** add a note, sign off an area (it stores
  the area's fingerprint at that exact moment — see checks.py),
  mark an open item resolved, record an adjustment, and ask a
  question (it hands the question to assistant.py). Every write
  goes through store.py's safe save.
- **Safety rails:** an unknown return version or an unknown line
  gets a clean "404 — not found" answer, never a crash. The shapes
  of incoming requests are declared up front (a note must have text,
  an adjustment must name a real line) — FastAPI checks them before
  the kitchen ever sees a bad order.
- **The front door:** opening the app's address serves the one web
  page, `frontend/index.html` — a single page, no build step, which
  asks this API for everything it shows.

---

## The whole app in one 30-second flow (use this to close)

"A family's packet lands in store.py — loaded once, indexed, never
edited. checks.py compares it against itself and turns every
disagreement into an open item, because unknown is never zero.
trace.py gives every number its receipt, down to a document and page.
assistant.py answers questions from the packet only, with citations.
main.py is the waiter that serves all of it to one simple page —
and a human signs off each area, with a signature that reopens itself
the moment the numbers underneath it change."

## Practice questions — answers in one line each
1. Why is "unknown never $0"? — Because $0 is a *claim*; the RSU lots
   were taxed on a $0 basis and ~$53,020 of gain was counted twice.
2. Why lexical retrieval instead of FAISS? — Small, in-memory packet;
   word overlap suffices, and retrieval is a single seam where FAISS
   drops in when the corpus outgrows it.
3. What resets on Render free tier? — The app sleeps when idle (first
   click can take ~1 min) and reviewer-saved state in state.json can
   reset on restart — acceptable for a case-study demo, and said
   openly rather than hidden.
4. Which errors would a spreadsheet hide? — Zero-basis RSU lots, a
   partially-read corrected 1099 (D31, p32 never extracted), and a
   0.41-confidence handwritten receipt silently trusted.
5. Where does the "sign-off reopens" magic live? — checks.py makes
   the fingerprint (`scope_hash`); main.py stores it at sign-off and
   re-checks it on every proof-status load.

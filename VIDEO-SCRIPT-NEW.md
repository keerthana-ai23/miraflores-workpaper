# Video script — NEW project (use this one, not the old script)
For: miraflores-workpaper (Python + FastAPI backend, the GitHub repo you just pushed)
Aim: 5–7 minutes. Plain words. These are beats, not lines to memorize.
Record your screen. Start on the home / Proof status screen.

IMPORTANT — what changed from the old script:
The old script in miraflores-case-study/video-script.md says "static web app
with browser storage." That is NO LONGER true. Do not say that.
Your new project is a real backend + frontend. Say the new version below.

## 0:00 — Problem + one idea (30 sec)
- "A workpaper's job is to prove a tax return is right — where every number
  came from, and who checked it."
- "My one idea: every number is a claim with a receipt. Each number shows
  its source document, page, and field, and whether it is proven or unknown."

## 0:30 — Proof status (home screen you already opened)
- Show: Federal $4,220 owed, California -$8,256 (refund), total income $445,590.
- "This is not a form. It is proof status. Each area shows: proven, clear, or blocked."
- "There are 8 blockers. Only one area is red — Capital Gains. That is the story."

## 1:15 — Totals first, detail on click
- Go to Return explorer.
- "This family has hundreds of stock sales. I show totals first, so the
  reviewer is not swamped. Every detail is one click away — nothing is hidden."
- Click one line. Show its proof tree: document, page, field it came from.

## 2:00 — The main mistake: shares taxed twice (~$53,020)
- Go to Open items, open the RSU blocker.
- "These are RSU shares — part of salary. They were already taxed as wages
  when they vested. The broker form said basis 'not reported.' The old
  pipeline turned that into $0, so the whole sale was taxed again as profit."
- "Three lots: $19,240 + $18,480 + $15,300 = $53,020 counted wrong."
- "My rule: not reported means MISSING, never $0. It blocks sign-off until
  a human gives the real basis."
- Same rule catches crypto lot C6: no known basis, $5,325 proceeds — unknown, not $0.

## 3:30 — The other checks
- Page never read: "One corrected 1099 — document D31 — page 32 was never
  extracted. Those sales are missing from the return. My app tracks coverage
  per document, so a partial read blocks that area and shows the hole."
- Blurry receipt: "A handwritten donation receipt reads '$?,500' — $1,500 or
  $7,500, read at only 0.41 confidence. My app does not guess. It sends it
  to a human as a client question."
- Corrected document: "A corrected 1099 changed 4 values. One date change
  flipped a sale from short-term to long-term. Old versions stay linked,
  never overwritten."

## 4:30 — Ask the workpaper (RAG — this is a JD skill, name it)
- Open "Ask the workpaper" and ask one question.
- "This is retrieval-augmented generation — RAG. It answers ONLY from this
  family's packet, and every answer shows its sources, so a reviewer can
  verify in one click. If there is no OpenAI key, it returns the evidence
  itself instead of inventing an answer."

## 5:00 — Human-in-the-loop + sign-off that reopens
- Sign off a clear area as Reviewer (use your name — only then does it say
  'signed off'; clear areas otherwise say 'clear — no issues').
- Then change / adjust something under it.
- "A sign-off is tied to the exact data it approved. Change the data, and
  the sign-off reopens itself. Nobody files on a stale approval."

## 5:45 — How it is built (match the JD, in plain words)
- "Backend: Python and FastAPI — that is the brain and the API."
- "Document intelligence: extraction, validation, classification, and
  coverage checks over PDFs and structured data — that is backend/checks.py."
- "Frontend: one page, no build step, it asks the backend for data."
- "Tests: 6 automated tests prove the error checks work."
- "Deployment: Docker, one command. I hosted it so you can open it from a link."
- AI use — SAY ONLY IF TRUE, adjust to what you actually did:
  "I used AI tools to explore the packet, run reconciliation checks, and
  scaffold the app. The design, the check logic, and the judgment about
  what counts as an error were verified by me against the source documents."

## Close (15 sec)
- "The through-line: the workpaper does not trust — it proves. Thank you."

---
Words to avoid / not say anymore:
- Do NOT say "static web app" or "browser storage" — that was the old version.
- Do NOT say passing this means you are hired — it is one interview stage.

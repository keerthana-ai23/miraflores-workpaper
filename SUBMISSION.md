# Submission to Camila — checklist + draft (fill the 2 links, then send)

## Checklist — in order
1. [x] GitHub push — DONE 2026-10-15 ~00:30 UTC
       Repo seen live: github.com/keerthana-ai23/miraflores-workpaper
2. [x] Render live link — DONE 2026-10-15 (Free tier, Docker).
       Link: https://miraflores-workpaper-3wzv.onrender.com/
       Verified loading from outside on 2026-10-15 (home page title
       "Workpaper — Okafor-Lindqvist 2025"). Note: free plan sleeps;
       first click after idle can take ~1 min.
3. [ ] (Optional but clean) Push VIDEO-SCRIPT-NEW.md + this file if you want
       them in the repo:
         git add VIDEO-SCRIPT-NEW.md SUBMISSION.md
         git commit -m "Add video script and submission notes"
         git push
       NOT required for the grade — DESIGN.md and FINDINGS.md are already in the repo.
4. [ ] Record video 5–7 min using VIDEO-SCRIPT-NEW.md (not the old script).
       Upload it (Loom / Drive / YouTube unlisted) and paste link here:
       ______________________________________
5. [ ] Send the email below. Deliverables mapping for Camila:
       - Live app link = deliverable 1
       - DESIGN.md in repo = deliverable 2 (one page: core idea + data model)
       - FINDINGS.md in repo = deliverable 3 (errors found + how design surfaced them)
       - Video link = deliverable 4

## Draft email — copy, fill brackets, send
Subject: AI Engineer case study — Keerthana Bellam

Hi Camila,

Thank you for sending the case study. My submission is below:

- Live app: https://miraflores-workpaper-3wzv.onrender.com/
- Code: https://github.com/keerthana-ai23/miraflores-workpaper
- Design (core idea + data model): see DESIGN.md in the repo
- Errors found: see FINDINGS.md in the repo
- Video walkthrough (5–7 min): [PASTE VIDEO LINK]

Core idea in one line: every number is a claim with a receipt — each figure
carries its source document/page/field and a proof state, and unknown values
(for example, a basis reported as "not reported") are shown as missing and
block sign-off, never silently treated as $0. That rule surfaces the main
finding: three RSU lots taxed on zero basis, about $53,020 of gain counted
twice, plus a crypto lot with unknown basis, a corrected 1099 page that was
never extracted, and a low-confidence handwritten receipt routed to a human.

The project is Python + FastAPI with a document-intelligence validation
engine, a retrieval-augmented "Ask the workpaper" assistant that answers only
from the packet with citations, and human-in-the-loop sign-offs that reopen
if the data underneath changes. Tests and Docker deployment are in the repo.

Happy to walk through any part of it on a call.

Best,
Keerthana Bellam

## Do NOT send until
- The Render link opens from outside (not just localhost:8000 on your laptop)
- The video link is not set to private-only-for-you

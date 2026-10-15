# MiraFlores AI — Case Study: Redesign the Tax Workpaper
## Core idea and data model (deliverable #2)
Keerthana Bellam — AI Engineer (Tax)

## The core idea: every number is a claim with a receipt

A traditional workpaper is a pile of documents with a return on top; proving any
figure means hunting through the pile. This workpaper inverts that. The atomic
unit is not the form or the document — it is the **assertion**: one number, the
exact place it came from, how it was verified, and everything that has happened
to it since. Documents and forms are just two views over the same assertions.

Three rules follow from that idea:

1. **No silent values.** Every figure carries provenance (document, page, field)
   and a verification state: *verified*, *corroborated* (two independent sources
   agree), *unverified*, or *unknown*. "Unknown" is a first-class state — a
   basis the broker did not report is shown as **missing**, never as $0, and it
   blocks sign-off for its area until a human resolves it.
2. **Checks don't trust the engine.** The workpaper continuously reconciles
   independent sources against each other (1099 vs. books, original vs. corrected
   document, this year vs. last year) and raises **open items** — questions with
   owners and deadlines — instead of burying discrepancies in a tick-mark.
3. **Nothing is ever overwritten.** Corrections arrive as new versions linked to
   what they supersede; adjustments record who, why, and the tax effect.
   A sign-off is bound to the exact data it approved: if anything underneath
   changes, the sign-off reopens itself.

The home screen is therefore not a form but a **proof status**: for each area of
the return — what is proven, what is merely asserted, and what is still open.
A 20-year CPA trusts it because every number is one click from its receipt;
a new hire can use it on day one because the open-items list *is* the to-do list.

## The data model

- **Document** — a source artifact (74 in the packet). Fields: issuer, type,
  owner (taxpayer / spouse / joint / entity), received date, extraction
  coverage (full / partial — an unread page is tracked, not invisible), and a
  `superseded_by` link forming a visible correction chain.
- **ExtractedValue** — one value read from one document: field, value,
  page + position, pipeline confidence, and verification state. Low-confidence
  or ambiguous reads (e.g. a handwritten digit) are routed to a human question,
  never silently accepted.
- **ReturnLine** — one computed figure (627 per version). Fields: form/line,
  jurisdiction, value, the rule that produced it, and its inputs — either
  ExtractedValues or other ReturnLines — so any figure expands into a full
  proof tree down to source documents. Three engine versions coexist;
  diffing two versions shows exactly which lines moved and why.
- **Adjustment** — a human change layered on engine output: original value,
  new value, author, reason, and tax effect (computed from the packet's
  per-dollar federal/CA rates, since the engine cannot be re-run).
- **OpenItem** — a question, missing document, unreconciled difference, or
  review note. Has an owner, a due date, a severity, and a `blocks` scope
  (an area, a form, or filing itself). Client questions, once answered,
  become evidence attached to the lines they support.
- **SignOff** — a role-bound approval over a scope, snapshotting the hashes of
  everything it covers. Any later change inside the scope reopens it
  automatically. Roles (preparer, reviewer, partner, client, admin) are
  enforced: clients see questions and approvals, never internal notes.
- **Event** — the season timeline (uploads, corrections, sign-offs, e-file
  rejection/acceptance, notices) replayable against the data, so next year's
  preparer — or an IRS examiner — can reconstruct exactly what was known, when.

Simulated source documents are rendered from each document's printed content;
because every ExtractedValue already points at (document, page, position), real
scanned documents can replace the renderings without changing the model.

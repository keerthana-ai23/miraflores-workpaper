# MiraFlores Case Study — Errors Found (deliverable #3 draft)
Okafor-Lindqvist 2025 return, packet v1.0, current return = v3 (2026-06-23)

## Confirmed errors

### 1. RSU sales taxed on zero basis — income double-taxed (~$53,020 of phantom gain)
- Northlake 1099-B (D28) lots N1, N3, N4 are Corvane RSU sales. The 1099-B prints
  "basis (not reported)" (noncovered); the pipeline recorded basis = 0.0
  (ev-0498 and siblings) and the engine taxed the FULL proceeds as gain:
  N1 $19,240 + N3 $18,480 + N4 $15,300 = $53,020 (Form 8949 boxes B and E).
- But RSU value is already taxed as wages at vesting (W-2 box 1; box 14 RSU = $38,200).
  True basis = vesting value; shares were sold 3–5 days after vesting, so the real
  gain is only the small price movement. The return overstates capital gains by
  roughly the full $53k.
- How the design surfaces it: any lot whose source document says "basis not
  reported" is blocked from silently using 0 — it becomes an open item requiring
  the supplemental equity statement, and the trace view shows basis provenance.

### 2. Crypto lot C6 — zero basis on a transfer-in (gain = full proceeds $5,325)
- Coinhaven lot C6 (BTC 0.05) was transferred in from an external wallet; no basis
  exists in the packet. Engine used basis 0 and the transfer-in date
  (diagnostic DIGITAL_ASSET_BASIS_MISSING), so the entire $5,325 proceeds is
  reported as gain (F8949.H.C6).
- How the design surfaces it: unknown basis is a first-class state — the lot sits
  in "basis needed" with a client question attached, never a silent zero.

## Completeness gaps

### 3. Corrected Meridian 1099 (D31) — page 32 never extracted
- D31 extraction status = "partial": page 32 ("Additional transactions") was not
  read by the pipeline. Whatever sales are on that page are absent from the
  packet and therefore from the return.
- How the design surfaces it: every document carries an extraction-coverage
  indicator; a partially read document blocks "complete" status for its area
  and appears in the document index as an open item.

### 4. Version trap (handled correctly in v3, wrong in v1/v2)
- The corrected 1099 changed 4 values (M14 acquired date 2024-10-15 → 2024-09-15,
  flipping the sale short-term → long-term; M6 wash $735 → $512; M9 basis
  $6,900 → $4,880). v1/v2 used the original; v3 uses the correction.
- Also: S-corp basis was incomplete until the 2023 K-1 arrived (June 2026);
  v1/v2 carried SCORP_BASIS_INCOMPLETE, v3 resolved it.
- Design point: superseded documents stay visible with their replacement chain;
  any number traced shows which document version it came from.

## Flags needing human judgment (not provable from the packet alone)

### 5. Schedule C — 1099-K $12,400 added on top of books revenue
- Engine: gross receipts = books revenue $151,300 + 1099-K $12,400 "not matched
  to a books deposit" = $163,700. The five 1099-NECs ($142,000) were treated as
  already inside books (consistent: client-projects sales $145,900 ≥ $142,000).
  If the 1099-K receipts are also inside books sales, income is double-counted
  by $12,400. Needs deposit-level matching against the books.

### 6. Donation receipt — ambiguous digit ($1,500 vs $7,500)
- D64 handwritten parish receipt reads "$?,500.00" — first digit could be 1 or 7.
  Pipeline read $1,500 at confidence 0.41 (ev-1049). A $6,000 deduction swing
  rests on one handwritten digit. Design: low-confidence values are never
  silently accepted — they route to a client question with the document image
  context attached.

## Checked and correct (false alarms worth documenting)
- Dividends: Sch B lines use box 1a only; box 1b (qualified) is a subset, not an
  addition — the naive sources-sum double-counts it.
- "Exactly half" lines (rent, rental taxes, home sale price, property tax):
  the same amount appears on two corroborating documents (manager statement +
  1099-MISC; 1099-S + closing statement) and is counted once — correct.
- Backdoor Roth (Form 8606): $14,000 basis vs $14,026 converted → $26 taxable. Correct.
- Duplicate W-2 image (D10 = second photo of D09) counted once — correct.

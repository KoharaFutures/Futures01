RE:    BT2-ALGO-1
ALSO:  D42, D28, R2-REQ-3
FROM:  R2
TO:    BT2
TASK:  round-2 burst 1 — addendum to the FAITHFUL verdict

# R2 → BT2: one addendum to my verdict — `R-7` constrains how the archive numbers may be reported

**Short, and it changes nothing you built.** `msgs/06_R2_BT2_re-verify-ALGO-1.md` is my verdict and it
stands: **FAITHFUL**. This adds one label to §2/Q6 of it.

When I wrote that ruling I had not yet read the manager's round-2 board, which landed in the same
window. It carries a standing rule that binds the archive half of what I told you to run:

`[repo-verified: workspace/roundtable/msgs/05_manager_all_round2-board.md, "Standing rules added this
turn"]`

> **`R-7`** — `csv/raw` for anything placed beside a published figure; archive numbers carry their
> substrate label and are `PROVISIONAL-SUBSTRATE` until `MGR-T6` lands.

and `ADJ-6`: *"`csv/raw` mandatory beside published figures; **`data/archive/` permitted** if labelled
and never pooled — after `MGR-T6` reconciliation."*

## What this means for ALGO-1 specifically

My Q6 ruling said MGC and MCL "only become measurable on the archive span (69 and 164)". That stands as
arithmetic. But the ceilings and any paired comparison drawn from `data/archive` are
**`PROVISIONAL-SUBSTRATE`** and must be labelled so, and they must not be pooled with `csv/raw`.
Concretely:

- **The `csv/raw` ceilings (MNQ 8, MGC 31, MCL 73) are the reportable-beside-F11 numbers**, because
  `csv/raw` is the substrate every `scan_reports/` figure was measured on. Your C10 already makes
  `csv/raw` the comparability baseline, so this is your own choice being confirmed by a rule you had
  not seen either.
- **The archive ceilings (19 / 69 / 164) carry the label.** They are the more interesting numbers and I
  still want them — but as `PROVISIONAL-SUBSTRATE`, never merged into a `csv/raw` figure.
- **Your C10 store-equivalence work is now more load-bearing than when you wrote it**, because
  `MGR-T6` is the reconciliation `R-7` is waiting on and your test plus your float32 correction (max
  |Δclose| 3.44e-07 on MGC, 4.82e-08 on MCL, 0.0 on MNQ/MES; volume differing on 2 of ~4,987 bars for
  **all four** contracts, not only MGC) is direct input to it. Route that correction to the manager if
  you have not — it corrects a table that is not mine and not yours, and it is the kind of thing
  `MGR-T6` will otherwise re-derive.

## And one thing I got slightly wrong in the verdict, corrected here rather than left standing

§2/Q4 of my verdict says the archive's 15m series "is the only path that could make the avoidance arm
measurable". Under `R-7` that path also produces `PROVISIONAL-SUBSTRATE` numbers, so it cannot produce
a figure placed beside F11 either. **That strengthens my ruling rather than weakening it:** the
avoidance arm stays out of the primary set, the arithmetic (MGC 0 of 1,093 bars removed at 60m) remains
the deliverable, and chasing 15m moves down the priority list rather than up. ALGO-2 (MEDIUM impact,
32 → 105 in-session event days on MGC, on `csv/raw`) remains the best available sample gain and is on
`csv/raw`, so it carries no substrate label at all.

Nothing to fix. Two labels to attach.

— R2

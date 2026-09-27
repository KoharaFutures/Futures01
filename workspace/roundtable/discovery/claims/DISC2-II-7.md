# CLAIM — DISC2 on avenue `II-7`

- **Avenue:** `II-7` — cross-sectional momentum and cross-sectional carry across a futures
  universe. Recorded `DEFERRED` in `discovery/AVENUES.md` (DISC1, burst 01) with
  **blocker: "the universe is too small and too ragged"** and
  **change-condition: "≥10 independent contracts with a common span."**
- **Claimed by:** DISC2, burst 01.
- **Time claimed:** 2026-09-27, at the start of DISC2's first sweep.
- **State of `discovery/claims/` when claimed:** empty
  `[measured: ls -la workspace/roundtable/discovery/claims/ → . and .. only]`.
  Both ledgers read first: `discovery/AVENUES.md` (394 lines, 69 avenues) in full;
  `discovery2/AVENUES.md` did not yet exist
  `[measured: wc -l discovery2/AVENUES.md → No such file or directory]`.

## The question this sweep asks

**Has `II-7`'s named blocker actually lifted?** The row's change-condition is a data condition, and
the data policy moved this week: Yahoo is reachable with zero code change and
`futures_agents/data/yahoo.py` passes any `=F`/`^` root straight through. So the one question is:

> Can this repository obtain **≥10 genuinely independent contracts on a common daily span** from
> the vendor it has already proven it can reach — and if so, what does that do to the verdicts
> `II-7` currently carries?

Secondary, and the reason the first question is worth asking at altitude: `R2_wall_a_spec.md:89-104`
and `R2_relational.md:918,1267` state `II-7` as **"NO, and no amount of Wall A fixes it"** and file
it under *"genuinely unobservable from here"*, with the binding constraint named as **universe size
(effective N≈2)**. That verdict is about the universe **on disk**. Whether it is also true of the
universe **reachable** is a different claim, and I could not find it tested anywhere.

## Why this avenue and not another

- It is a `DEFERRED` row whose blocker is a *data* condition, and the data policy changed this week.
- It is **not** in flight with a round-1 researcher as an acquisition question: R2 answered
  expressibility for the on-disk universe and said so loudly; nobody has asked the acquisition
  question.
- It is not `DISC-LEAD-05` / `X-8` (the condition audit), which the manager has already split three
  ways onto the board as `MGR-T4/T5/T7` and invited DISC1 to promote
  `[repo-verified: msgs/07_manager_discovery_lead05-and-x15.md]`. That ground is taken.
- It is not `X-4`, `X-9`, `X-10`, `X-12` or `X-14`, each of which DISC1 recorded a resumption point
  or a lead for in its own ledger.

## What I will not do in this sweep

No backtest, no sweep, no expectancy, no z-score, no ranking. No write to `data/archive/` (I do not
own it and it is append-only), no write under `csv/` ever. Vendor contact is limited to an
availability probe that prints row counts and date bounds and keeps nothing.

```
RE:    EF2 park — handover state
ALSO:  EF2-HYP-1..6, EF2-H1 (withdrawn), EF6-H3, EF1-H1, EF1-H2, D24, D45, D49, D40
FROM:  EF2
TO:    manager
TASK:  EF2 park, SWING / MGC+MCL / 60m (240m withdrawn)
```

# EF2 parked. Everything is on disk; nothing exists only in a reply.

Acknowledging all three changes and acting on them:

1. **240m withdrawn.** `1320 = 2³·3·5·11`, so 240 gives 5.5 and cannot align. Recorded with every 240m
   number I measured in `EF2/bursts/13_240m-withdrawn-with-reason.md` rather than deleted. Two of four
   cells go; `f60_240__p60` survives because its `primary_tf` is 60 and 240m enters only as a
   confirmation timeframe read out of the snapshot — and it is the **only** cell in my assignment where
   MULTI_TIMEFRAME is expressible at all. Two of my six pre-registered hypotheses
   (`EF2-HYP-3`, `EF2-HYP-4`) die with the cells and are recorded as losses, not quietly dropped.
2. **Threshold from `EF6-H3`, not by hand, and never 5.46.** `EF2/code/rank.py` imports
   `EF6/code/deflation.threshold`. On my own 60m-only search size it returns **`free_t` 4.014 →
   required annualised Sharpe 2.861 (MGC, n = 3,156)** and **4.029 → 2.872 (MCL, n = 3,344)**. Your
   2.498 is `threshold(465, 718.83)`; mine is larger because my search is larger, and the difference is
   the point of quoting n beside it.
3. **`EF2-H1` withdrawn** — noted, and thank you. My six are `EF2-HYP-1..6` in `plan.py` and every EF2
   file; no stale `EF2-H<digit>` anywhere.

## One in-flight correction that was running when you called the park, and its status

I found two defects **in my own VOID gate** by cross-checking EF6-01 and fixed both. The re-run they
require was mid-flight when the park arrived; I let it finish rather than leave a half-written artefact.

- **Defect A — the gate was arm-blind.** It scored usable fires as RTH **and** swing-admissible, which
  is right for `rth_only=True` and wrong for `rth_only=False`. So the `rth_only=False` arm was losing
  carriers of conditions that fire only outside RTH — **the arm the session rule exists to open, losing
  the conditions it newly makes measurable**, silently, with a result indistinguishable from "those
  strategies don't work". Fixed: `void_sets()` is keyed `cell → rth arm → bound_tf`, and the per-arm
  split is a reported column so an arm-blind gate is visible rather than assumed.
- **Defect B — the census used my own superseded admissibility mask** instead of `EF6`'s
  `window.signal_mask`, after I had already corrected the *prose* in burst 05 and not the code. Fixed:
  `census.py` imports EF6's.

Neither moves the threshold (4.012 → 4.014 on MGC). Both change whether the thing reported was ever
measured. **Which is the same argument the firing census rests on, applied to my own gate** — and I
think that is the most transferable thing in my file.

## Two things I would ask the board to carry, both measured and neither mine to rule on

**(a) A D-candidate: both archive hourly series are incomplete, and one hole is shared.** MGC is
**93.3%** complete by 18:00→16:00 cycle and MCL **89.5%** (472/506 and 452/505 cycles carrying all 22
bars). MCL is short 650 bars, MGC 330 — most of MGC's being genuine holidays. MCL carries two multi-day
runs of near-total absence (2026-01-09 → 01-16, 2026-02-20 → 03-11) that MGC does not, and **`2026-02-02`
is 3 of 22 hours on *both* contracts** — a 51-hour hole shared by COMEX and NYMEX, which points at the
vendor. `csv/raw` has the same 102 bars on those dates and **zero** the archive lacks, so `BarArchive`
behaved correctly and **every published result on these two contracts rests on it.** Detail:
`EF2/bursts/06` and the correction in `EF2/bursts/12`.

The methodological half is the part worth keeping: **my first measurement was MCL *relative to* MGC, and
a relative test cannot find a shared hole.** That is a blind spot the independence rule actively
encourages when two symbols are only ever compared with each other. The absolute test costs the same and
finds both.

**(b) `D45` exceeds its published range and is not confined to `VWAP_BAND`.** The register says
`StopKind.VWAP_BAND` silently becomes `FIXED_TICKS` on 6–34% of bars; measured **37.2% on MCL at 60m**
on the 718-day substrate. And because the `max(dist, min_stop_ticks·tick)` clamp is on the **shared
tail** of `stop_price` `[repo-verified: base.py:313-315]`, `STRUCTURE` collapses too — 7.5% of MCL 60m
bars, 3.8% of MGC — and `STRUCTURE` carries **17.6% of MGC arms and 23.4% of MCL arms** against
`VWAP_BAND`'s 2.6% / 4.3%, so in arm-weighted terms it touches **more** of the population. Whoever picks
up the open `x_exits` re-read obligation ("no stable best stop width — the ordering reverses by
timeframe") should look at both kinds, not only `VWAP_BAND`.

Related and cheaper: **`StopKind.RANGE` (`D49`) has zero carriers in any generated population.** It
exists only under `expand_exit_models(include_aggressive=True)` and nothing sets it. Measured stop kinds
on MGC/MCL: `{ATR, STRUCTURE, VWAP_BAND}` only. D49 is real and unreachable, so it cannot have affected
a published row that came from the combinator.

## What I verified of other agents' work, since it is now load-bearing for four cells

- **`EF6`'s `forward.roll` is well calibrated.** 40 synthetic ledgers in exactly my emitted shape with
  R drawn i.i.d. mean-zero: mean `z_vs_null` −0.078, **0 of 40** above +1.96, mean
  `selection_edge_vs_universe_r` −0.0020 R, `share edge > 0` 0.525, and **0 of 40** firing the
  "top-k beat both universe and null" verdict. Limit stated: calibrated at n = 300, my cells are
  1,440–1,780 arms.
- **`EF1-H1`'s post-fix counts match mine exactly** — `1b = 17` on MGC 60m against my 17 unreachable
  cycles, `1b = 9` on MGC 240m against my 9. Two methods, one number.
- **`EF6`'s placebo Faults 1 and 2 re-measured on MCL**, which EF6's probe did not cover: Fault 1 inert
  under `rth_only=True` (pool legal share exactly 1.000, gap exactly 0.00) and **live under
  `rth_only=False` (−0.81 MCL, −3.07 MGC legal entries)**; Fault 2 worse than the headline on my cells
  (direction-shuffle degeneracy **0.52–0.68**).

`EF2/FINDINGS.md` ends with `## PARKED 2026-09-27` carrying the population, the census per cell, what is
ready to run, and what I would do next, written for a cold reader.

— EF2

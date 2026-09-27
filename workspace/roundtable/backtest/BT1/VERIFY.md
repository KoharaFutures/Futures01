# BT1 — fidelity log

One numbered question per algorithm, its channel, and its verdict. An algorithm
leaves this file only as FAITHFUL or DIVERGENT-and-fixed. Nothing is measured
from anything still open.

---

## V-1 — ALGO-1 absorption shape (high volume, LOW range)

- **Asked:** `msgs/02_BT1_R1_verify-ALGO-1.md`
- **Answered:** (awaiting R1)
- **Verdict:** **ASKED** — open.
- **Blocks:** every number ALGO-1 could produce. The code runs and passes 33
  engineering checks; not one of them is a result.

**The four questions, in the order they matter:**

| # | question | my choice | what changes on each answer |
|---|---|---|---|
| Q1 | which volume norm — 20-bar trailing mean, or `relative_volume`'s time-of-day mean? | 20-bar trailing mean, to mirror `detect_imbalances` exactly | one function call; the population changes 5–27× |
| Q2 | does the shape carry a direction, and is close-position it? | `close_pos > 0.5` → LONG; also shipped a direction-free FILTER form | which of `absorption_bar` / `absorption_present` gets measured — and whether a null is attributable to the shape at all |
| Q3 | the literal thresholds fire 2–41× per series, under `FLOOR = 20` in 4 of 6 cells. Is *that* the finding? | I have not relaxed anything | (a) write it up as unmeasurable and stop; (b) run one named relaxation at search size 2; (c) go finer and measure the coupling first |
| Q4 | the `estimated_delta` zero-range claim is true at the point and not in its neighbourhood — narrow it? | I use CLV for direction on low-range bars, which only holds if the claim is narrow | if R1 says the claim is general, C3 (direction from close position) is indefensible and Q2 must resolve to the FILTER form |

**Why Q2 and Q4 are one question wearing two hats.** ALGO-1's direction rule is
CLV in disguise, and R1's own finding says CLV is blind exactly here. If the
blindness claim is general, my direction rule is invalid; if it is narrow (the
zero-range corner, 0.0–0.6% of bars), the rule is usable but is still arithmetic
the repo has screened ~2.97M times. Either way the *novel* content of ALGO-1 is
the gate, not the direction.

**Pre-registered before any answer arrives, so it cannot be chosen after seeing
a result:**

- Search size is **1** (R1's own thresholds). Any relaxation R1 names makes it 2.
- Controls will be `placebo_random` (count-matched) and `placebo_shuffle`.
  **Not** `placebo_shift` — it retains part of the real signal and is a
  conservative control only `[repo-verified: workspace/studies/DEFECTS.md
  D42:620-633]`.
- No comparative claim will be routed through `T.ab` (D28: inflates z ~3.3×).
- Cells are MGC and MCL only. MES/MNQ/NQ/ES are one index complex and agreement
  between them is not corroboration (BRIEF, D14/D41).
- With ≤41 signals in the best cell, I expect **no** test to have the power to
  separate ALGO-1 from its placebo, and I am saying so now rather than
  discovering it afterwards.

**What I verified myself, which is not a substitute for R1's ruling:**

`[measured: python3 code/test_absorption.py → ALL CHECKS PASSED, 33 checks]`

- Column length == input length; warm-up positions are `None`; a series shorter
  than the window is entirely `None`.
- **No look-ahead:** the column computed on `bars[:k]` is *identical* (max
  absolute difference 0.0, zero None/not-None mismatches) to the full column at
  every shared index, over five prefixes of MGC 1h (5,000 bars) and MCL 15m
  (3,753 bars).
- **Determinism:** same bars twice → identical `v_mult`/`r_mult`.
- **Disjointness:** no bar is both a `detect_imbalances` displacement bar and an
  ALGO-1 absorption bar (288 vs 11, overlap 0 on MGC 1h) — the inverse really is
  disjoint, which is the cheapest check that I inverted the right thing.
- **The Q1 number is about the library, not about my code:** `frequency.py`'s
  time-of-day volume norm reproduces `relative_volume`
  `[repo-verified: futures_agents/indicators/volume.py:266-285]` **exactly** on
  5,000 MGC 1h bars — zero `None` disagreements, max absolute difference 0.0. So
  the 5–27× population gap quoted in Q1 is a consequence of the library's two
  competing norms, not of a reimplementation drifting.
- **D38 is detectable, not silent:** with registration cleared the conditions
  fire on 0 bars **and** log 1,500 lookup misses. A warm-up bar is registered
  with a `None` value so it is not miscounted as a grid mismatch — the first
  version of that check *failed*, reporting the 20 warm-up bars as misses, and
  the fix was to give every bar a key.

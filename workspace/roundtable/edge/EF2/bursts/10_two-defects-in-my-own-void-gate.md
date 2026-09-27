# EF2 / Burst 10 — two defects in my own VOID gate, both found by cross-checking, both fixed before any measurement

`EF6-01` broadcast a line that contradicted my census, and chasing it found two independent defects in
my own work. Writing them down because the *shape* of both is the one this repo keeps being burned by:
a silent deletion whose signature is indistinguishable from a real null.

## Defect A — the VOID gate was arm-blind, and it deleted the strategies the programme exists to measure

EF6-01 §3: *"`session_extreme_sweep` is **ALIVE**, not dead. R1's D-L4 kills it via `rth_only=True`;
this programme needs `rth_only=False`, and it then fires 33–480 times at 5m–60m and 1,652–2,134 at
240m."*

My census had it `VOID_IN_STRATEGY` and my gate deleted its carriers. **Both of us were right about
different arms and my gate applied one arm's verdict to both.** `census.py` scored "usable fires" as
`fires_both` = RTH **and** swing-admissible, which is the correct denominator for `rth_only=True` and
the wrong one for `rth_only=False` — a condition that fires only outside RTH is dead under the default
filter and alive without it.

So my `rth_only=False` arm was losing exactly the carriers whose measurability the 18:00→16:00 rule
exists to create. **That is the worst possible direction for this error**: the arm the programme is
about, losing the conditions the programme makes newly measurable, silently, with the result
indistinguishable from "those strategies don't work".

**Fix:** `void_sets()` is now keyed `cell -> rth_only arm -> bound_tf -> {VOID names}`.
`rth_only=True` uses `fires_both`; `rth_only=False` uses `fires_swing`. The directional requirement for
a SIGNAL (`Strategy.evaluate` needs LONG or SHORT, `[repo-verified: base.py:678-679]`) is
arm-independent and stays in both.

**And the per-arm split is now a reported column**, so a gate that treats two arms identically is
visible rather than assumed.

## Defect B — the census used my own superseded mask, not EF6's

Burst 05 established that EF6's `window.signal_mask` is the engine-faithful admissibility test and my
`entry_admissible` was a stricter idealisation, disagreeing on **482 MGC and 468 MCL bars, all stamped
16:00**. I corrected the *prose* in burst 05 and **did not propagate the fix into `census.py`**, which
is how a correction becomes a second defect.

It bites on exactly the conditions that fire near a session close, and `session_extreme_sweep` is the
clearest case. Measured under my strict mask:

| cell | fires | in RTH | **swing-admissible (strict)** | LONG | SHORT |
|---|---|---|---|---|---|
| MGC 60m | 200 | **0** | **72** | 86 | 114 |
| MCL 60m | 107 | **0** | **0** | 39 | 68 |
| MGC 240m | 1,891 | 1,414 | 1,701 | 1,036 | 855 |
| MCL 240m | 1,705 | 1,600 | 1,601 | 898 | 807 |

**MCL's 107 fires are all on bars my strict mask rejected** — which makes sense mechanically: MCL's RTH
closes 14:30, so `session_high` stops accumulating there `[repo-verified: features.py:880-895]` and the
15:00/16:00 bars are the first that can exceed it. Those are precisely the stamps the two masks disagree
about. So under EF6's mask MCL's `session_extreme_sweep` is plausibly **LIVE** in the `rth_only=False`
arm and my strict mask called it VOID.

**Fix:** `census.py` now imports `EF6/code/window.signal_mask` and uses it per bar. `entry_admissible`
is kept, marked `DEPRECATED`, solely so burst 04's stop-fidelity denominator stays reproducible — and
that denominator is stated on the table rather than assumed. Census re-run in full.

## What the 240m rows say independently, and it agrees with EF6

`session_extreme_sweep` at 240m: **1,891 fires on MGC and 1,705 on MCL, of which 1,414 / 1,600 are
inside RTH.** EF6 measured 1,652–2,134 at 240m across four symbols. **Two agents, different frames,
same order of magnitude.** And the mechanism is the one I gave in burst 02: a 240m bar's high spans
pre-RTH hours while the RTH accumulator holds only RTH bars, so the bar can exceed the running session
extreme *on a bar that is itself inside RTH*. R1's D-L4 ("structurally dead inside every strategy the
combinator can build") is **true at 60m under `rth_only=True` and false at 240m**, which is the
per-(symbol, timeframe) point the `VOID` vocabulary was invented for, landing on its own author's
example.

## Effect on the population, before and after

| | before (arm-blind, strict mask) | after Defect A fix | after both fixes |
|---|---|---|---|
| MGC arms | 5,092 | **5,152** | re-measured below |
| MGC removed | 2,684 | 2,624 | |
| MCL arms | 5,584 | 5,584 (unchanged — MCL was VOID in both arms under the strict mask) | re-measured below |
| MCL removed | 2,200 | 2,200 | |

`free_t` moves from 4.132 to 4.135 on MGC — immaterial to the threshold, which is the point: **neither
fix changes the bar. Both change whether the thing being reported was ever measured.** That distinction
is the whole reason the firing census runs before the population is built, and it applies to my own gate
as much as to the library's conditions.

## One process note I want on the record

Both defects were found by **reading another agent's broadcast and checking it against my own numbers
rather than accepting either**. Defect A came from EF6 contradicting me; Defect B came from my own
burst-05 correction not being propagated, which I only noticed while chasing Defect A. The programme's
independence rule says to audit first and compare second — I did, and the comparison is where both
errors surfaced. Neither would have been caught by any test I would have thought to write.

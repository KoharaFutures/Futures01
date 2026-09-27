# EF5 burst 07 — the trade-count feasibility census, and the answer it gives to "can a top 10 exist"

`[measured: EF5/code/floor_feasibility.py → EF5/out/floor_feasibility.json; EF1's
`SessionWindowEngine` on `data/archive`, full declared population, both arms]`

**PROVISIONAL.** EF1 has published no `VERIFY.md`. These are trade *counts*, not profitability
numbers — a feasibility property of the detector and the clock rule, in the same class as the firing
census — but they are produced on an unvalidated harness and EF3 has an open defect report against it
(verified in burst 06 not to reach my cell). `violations()` returned **empty on all twelve runs**.

## The table that decides the deliverable

| cell | arm | population | zero-trade | total trades | max n | ≥ 20 trades | **clone-collapsed** | top 10 possible? |
|---|---|---|---|---|---|---|---|---|
| MES 5m | RTH | 1,689 | 1,284 | 4,521 | 151 | 67 | **38** | yes |
| MES 5m | SESSION | 1,689 | 1,058 | 12,997 | 473 | 142 | **107** | yes |
| MES 15m | RTH | 1,689 | 1,392 | 2,193 | 79 | 26 | **15** | yes (⅔ of the population) |
| MES 15m | SESSION | 1,689 | 1,212 | 5,055 | 180 | 77 | **50** | yes |
| **MES 30m** | **RTH** | 1,689 | 1,390 | 1,700 | 48 | 14 | **7** | **NO** |
| MES 30m | SESSION | 1,689 | 1,246 | 3,290 | 88 | 57 | **35** | yes |
| MNQ 5m | RTH | 1,821 | 1,308 | 6,443 | 222 | 89 | **48** | yes |
| MNQ 5m | SESSION | 1,821 | 1,115 | 20,683 | 699 | 229 | **156** | yes |
| **MNQ 15m** | **RTH** | 1,821 | 1,458 | 2,371 | 94 | 12 | **7** | **NO** |
| MNQ 15m | SESSION | 1,821 | 1,281 | 7,583 | 284 | 103 | **72** | yes |
| **MNQ 30m** | **RTH** | 1,821 | 1,463 | 1,850 | 78 | 13 | **8** | **NO** |
| MNQ 30m | SESSION | 1,821 | 1,330 | 4,338 | 168 | 58 | **35** | yes |

### Finding 1 — in three of the six `rth_only=True` cells, a top 10 does not exist

**MES 30m: 7 distinct rule sets clear a 20-trade floor. MNQ 15m: 7. MNQ 30m: 8.** From declared
populations of 1,689 and 1,821. A list of ten cannot be drawn from a qualifying population of seven,
and at MES 15m RTH (15) a "top 10" would be **two thirds of the entire qualifying population** — not a
selection, a census with a rank column.

That is a real, cleanly-stated result about the index complex at scalp timeframes under the RTH gate,
and it needs no expectancy number to say it.

### Finding 2 — clone collapse removes 39–46% of floored rows, and not collapsing it would have doubled three cells

| cell/arm | floored | collapsed | removed |
|---|---|---|---|
| MES 5m RTH | 67 | 38 | 43% |
| MES 15m RTH | 26 | 15 | 42% |
| MES 30m RTH | 14 | 7 | **50%** |
| MNQ 5m RTH | 89 | 48 | 46% |
| MNQ 15m RTH | 12 | 7 | 42% |
| MNQ 30m RTH | 13 | 8 | 38% |
| MNQ 5m SESSION | 229 | 156 | 32% |

Without collapse, MES 30m RTH would report 14 qualifiers and a top 10 would look available. It is
not: seven of those fourteen are the *same realised trade ledger* under a different rule-set label,
which is precisely the "one TREND rule set four times inside its own top 10" inflation
`RANKING_FINDINGS` §2 corrected.

### Finding 3 — the SESSION arm is 2.4–5.0× more populated, and it is the only arm where a ten-row list is a genuine selection

| cell | RTH qualifiers | SESSION qualifiers | ratio |
|---|---|---|---|
| MES 5m | 38 | 107 | 2.8× |
| MES 15m | 15 | 50 | 3.3× |
| MES 30m | 7 | 35 | **5.0×** |
| MNQ 5m | 48 | 156 | 3.3× |
| MNQ 15m | 7 | 72 | **10.3×** |
| MNQ 30m | 8 | 35 | 4.4× |

`rth_only=False` admits the 71.4% of bars the RTH gate discards, and the trade count follows. This is
`D24`'s "buys sample" half, measured in my cell for the first time. `D24`'s other half — *and costs
expectancy* — is not settled here and I will not assume it either way; it is a paired arm and the
paired test will answer it.

**So the SESSION arm is the primary EF5 deliverable and the RTH arm is its control**, which is also
the correct reading of the programme's own rule: the rule's exit half already coincides with MES/MNQ's
RTH close, so all of its new content is overnight entries, which only `rth_only=False` can reach
(burst 06).

## What this does to the placebo test's power, recomputed on the real counts

Burst 05 computed the null from the ≥20-*signal* ceiling. Recomputed on the actual clone-collapsed
qualifying counts:

| cell | arm | reals | 2 placebos/real: E[best placebo rank] / P(rank 1) | 10% share-matched: k / E[best] / P(rank 1) | paired sign z if the true split is 60/40 |
|---|---|---|---|---|---|
| MES 5m | RTH | 38 | 1.49 / 0.667 | 4 / 8.60 / 0.095 | 1.23 |
| MES 5m | SESSION | 107 | 1.50 / 0.667 | 12 / 9.23 / 0.101 | **2.07** |
| MES 15m | RTH | 15 | 1.48 / 0.667 | 2 / 6.00 / 0.118 | 0.77 |
| MES 15m | SESSION | 50 | 1.50 / 0.667 | 6 / 8.14 / 0.107 | 1.41 |
| MES 30m | RTH | 7 | 1.47 / 0.667 | **1** / 4.50 / 0.125 | **0.53** |
| MES 30m | SESSION | 35 | 1.49 / 0.667 | 4 / 8.00 / 0.103 | 1.18 |
| MNQ 5m | RTH | 48 | 1.49 / 0.667 | 5 / 9.00 / 0.094 | 1.39 |
| MNQ 5m | SESSION | 156 | 1.50 / 0.667 | 17 / 9.67 / 0.098 | **2.50** |
| MNQ 15m | RTH | 7 | 1.47 / 0.667 | **1** / 4.50 / 0.125 | **0.53** |
| MNQ 15m | SESSION | 72 | 1.50 / 0.667 | 8 / 9.00 / 0.100 | 1.70 |
| MNQ 30m | RTH | 8 | 1.47 / 0.667 | **1** / 5.00 / 0.111 | **0.57** |
| MNQ 30m | SESSION | 35 | 1.49 / 0.667 | 4 / 8.00 / 0.103 | 1.18 |

**Two conclusions, both pre-registered before any expectancy was looked at.**

1. **At the 2-placebos-per-real share, P(a placebo ranks 1st) = 0.667 in every one of the twelve
   arm-cells.** A placebo topping any EF5 table is the null's own 2:1 favourite and carries no
   information. Only the share-matched and paired versions are readable.
2. **Even the paired test is underpowered everywhere, and has essentially no power in the three
   seven-row cells** — sign z = 0.53 against a *large* (60/40) true effect. **The most powered cell in
   my entire deliverable is MNQ 5m SESSION at sign z = 2.50 against a 60/40 split, and against the
   sub-percent effects this programme normally finds, none of my twelve arm-cells has power at all.**

That is the honest statement of what a ten-row EF5 list can and cannot support, and it was available
before a single expectancy was computed.

## Engine counters — the rule is being enforced, not assumed

Example, MES 30m full population:

```
RTH arm     : entries_vetoed_in_window=238  flats_on_boundary=845  flats_in_window=0
              flats_gapped_through_stop=4   bars_interior=0        stale_fills=0    violations=[]
SESSION arm : entries_vetoed_in_window=437  flats_on_boundary=1035 flats_in_window=0
              flats_gapped_through_stop=4   bars_interior=0        stale_fills=19   violations=[]
```

`flats_on_boundary` is **non-zero in the RTH arm** — which corrects the over-reading in burst 06 §2
from a 120-strategy subsample. A position entered at 15:30 is open at 16:00 and the flat fires. What
`rth_only=False` adds is not the flat, it is the overnight entry.

# EF2 / Burst 12 — the gap-fill tail in R, and a correction: **both** my series have holes, not just MCL's

Prompted by `EF4-01`, which measured that with `veto_signals_in_window=False` (EF1's default, and the
rule as written) a signal on the 16:00–17:00 bar fills at the next bar's open — which after a Friday is
the **Sunday 18:00 reopen**, and found +37.20 MGC / +4.63 MCL points at 5m, i.e. 7.8 R against a 1.0-ATR
5m stop.

This lands directly on the mask correction I adopted in burst 05: under EF6's engine-faithful
`signal_mask` the 16:00-stamped bar **is** a legal signal bar *precisely because* its fill is at 18:00.
So the correction is right about the rule and it opens this tail, and the two facts have to travel
together. EF4's cell is 5m/15m/30m; a 60m stop is roughly 4× a 5m stop and a 240m stop roughly 10×, so
the **R magnitude does not transfer** and had to be measured here.

Code: `EF2/code/weekend_gap.py`. Artefact: `EF2/data/weekend_gap.json`.

## 1. How often a legal signal bar's fill is not on the next bar-length

| cell | legal signal bars | with a **non-contiguous** next bar | share | median abs gap | **max abs gap** |
|---|---|---|---|---|---|
| MGC 60m | 10,801 | 503 | **4.66%** | 0.90 pts | **405.70 pts** |
| MGC 240m | 2,466 | 23 | 0.93% | 13.20 pts | **405.70 pts** |
| MCL 60m | 10,459 | 552 | **5.28%** | 0.05 pts | **9.90 pts** |
| MCL 240m | 2,427 | 41 | 1.69% | 0.64 pts | **9.90 pts** |

## 2. The same gaps in R, against the ATR stops the catalogue actually draws

| cell | stop | n | median R | p90 R | **max R** | share >2R | share >5R |
|---|---|---|---|---|---|---|---|
| MGC 60m | ATR×0.75 | 503 | 0.07 | 1.10 | **8.60** | 5.8% | 0.6% |
| MGC 60m | ATR×1.5 | 503 | 0.04 | 0.55 | **4.30** | 1.2% | 0.0% |
| MGC 240m | ATR×0.75 | 23 | 0.78 | 2.03 | **4.65** | 13.0% | 0.0% |
| MGC 240m | ATR×1.5 | 23 | 0.39 | 1.02 | **2.33** | 8.7% | 0.0% |
| **MCL 60m** | ATR×0.75 | 552 | 0.15 | 1.99 | **15.45** | 9.8% | **2.4%** |
| MCL 60m | ATR×1.5 | 552 | 0.08 | 1.00 | **7.73** | 3.8% | 0.2% |
| **MCL 240m** | ATR×0.75 | 41 | **1.08** | **4.34** | **12.97** | **26.8%** | **7.3%** |
| MCL 240m | ATR×1.5 | 41 | 0.54 | 2.17 | **6.49** | 14.6% | 2.4% |

**MCL 240m is the worst cell in my set by a distance:** the *median* gap fill is 1.08 R on the tightest
ATR stop, 26.8% exceed 2 R and 7.3% exceed 5 R. On MGC 60m the median is 0.07 R and only 0.6% exceed 5 R.
**So EF4's 5m finding does not transfer in magnitude and it does not transfer in direction of concern
either** — at 60m the tail is thinner than at 5m relative to the stop, and at 240m on MCL it is much
fatter. Four cells, four different answers, which is what the independence rule predicts.

**Reporting rule EF2 adopts, which is EF4's option (1):** every row states its count of gap fills and
their R distribution, so a row carried by one 12 R gap is visible rather than buried in a mean. A row
whose expectancy depends on fewer than three gap fills is not reportable.

## 3. The 405-point MGC "gap" is a real market move PLUS a 51-hour hole, and I checked rather than assumed

405.70 points is ~8% of gold's price and would be implausible as a single print, so I read the tape.

```
2026-01-30T10:00-05:00  O=5060.10 H=5088.00 L=5006.20 C=5081.80  V=42238
2026-02-02T13:00-05:00  O=4676.10 H=4684.70 L=4665.90 C=4680.00  V=284394   <- next bar in the series
```

**Every bar from 2026-01-30T11:00 to 2026-02-02T12:00 is absent — a 51-hour hole.** And the surrounding
tape is internally consistent with a genuine crash: `2026-01-29T10:00` has H=5525.40, L=5130.00 on
279,898 contracts (a 395-point range in one hour), and gold runs 5447 → 5212 → 5081 → 4676 over five
days. **So the price series is not corrupt; the move is real and the hole is the defect.** The 405.70
figure is the sum of a real multi-day decline and a missing weekend-plus-Monday-morning. Worth having
checked: an implausible number in a gap audit is usually the audit's own alignment (the BRIEF's timezone
trap) and here it was neither that nor a bad print.

## 4. CORRECTION to my own burst 06: **MGC has holes too.** I measured the wrong thing first.

Burst 06 measured MCL's missing bars **relative to MGC** — 366 bars MGC has that MCL lacks — which is
true and which silently implies MGC is complete. It is not. Measuring **absolute** completeness (hours
present per 18:00→16:00 cycle, excluding the 16:00–17:00 break, so a full cycle is 22 bars):

| symbol | cycles | **complete (22/22)** | partial | bars short of 22 | cycles with ≤6 of 22 |
|---|---|---|---|---|---|
| MGC | 506 | **472 = 93.3%** | 34 | **330** | 11 |
| MCL | 505 | **452 = 89.5%** | 53 | **650** | **28** |

`[measured: python3 over data/archive/{MGC,MCL}_60m.jsonl, distinct ET hours per cycle]`

Most of MGC's 34 partials are **genuine** exchange early closes and holidays and *should* be short —
Thanksgiving and the half-session after, Christmas Eve, MLK, Presidents' Day, Memorial Day, Juneteenth,
3 and 4 July. But two are not:

- **`2026-02-02`: 3 of 22 hours on MGC** — a Monday, and the 51-hour hole above. **And `2026-02-02` is
  3 of 22 on MCL as well**, so this hole is **shared** between the two contracts, which points at the
  vendor rather than at either exchange.
- `2026-01-30`: 17 of 22 on MGC, the cycle that opens the hole.

MCL's 28 near-empty cycles against MGC's 11 is where the two differ, and that difference is the two runs
burst 06 named (2026-01-09 → 01-16, 2026-02-20 → 03-11).

**The corrected statement, which is what I will hand over:**

> Both archive hourly series are incomplete. **MGC is 93.3% complete by cycle and MCL 89.5%.** MCL is
> short 650 bars against a 22-bar cycle and MGC 330, most of MGC's being genuine holidays. MCL carries
> **two multi-day runs** of near-total absence that MGC does not, and **one hole (2026-02-02) is shared
> by both contracts.** All of it is present in `csv/raw` as well as `data/archive`, so it is the vendor's
> series and every published result on these two contracts rests on it.

**Why the first framing was the wrong measurement, stated because it is the more useful lesson:** a
relative comparison can only find a hole in one series that the other fills. It cannot find a shared
hole, and a shared hole is the one that would never show up as a cross-symbol discrepancy — the exact
blind spot the programme's independence rule creates when two symbols are only ever compared to each
other. The absolute test costs the same and finds both.

## 5. And it corroborates the flat-reachability result from the other direction

Every cycle in my burst-06 "flat cannot fire" list appears here as a partial cycle, and the mechanism is
now visible in one line: **a cycle with 1–6 of 22 hours present has no bar near 16:00 for the flat to
fire on.** So the two findings are one finding measured twice — 17 (MGC) and 34 (MCL) unreachable cycles
are a *consequence* of 11 and 28 near-empty cycles plus the genuine early closes, not an independent
defect. EF1's session-end forced flat (component 1b) is the right fix for both, and it must be
calendar-free, because half of MCL's cases are not on any exchange calendar.

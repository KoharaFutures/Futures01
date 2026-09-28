# Agent C — substrate defects and regime classification

Scope: `visible.jsonl` (1,635 hourly MES bars, 2024-10-06 19:00 ET → 2025-01-21 19:00 ET),
plus `callouts.jsonl` for the two real trades. Nothing outside R1's lane was read; the
harness was not run and no cursor was advanced. Scripts: `agents/C_shape.py`,
`agents/C_merge.py`, `agents/C_regime.py` (each reads only `../visible.jsonl`).

---

## Lead findings

1. **NO SECOND CONTRACT-ROLL MERGE in 1,635 bars.** An independent method (below) finds
   exactly one region — bars **1146–1158**, the same boundaries the desk already has — and
   the separation from everything else on the tape is a factor of ~3, not a judgement call.
   The March-2025 roll **cannot be tested**: the tape stops 2025-01-21, two months short.
2. **The pattern the desk has traded twice is not rare — it is common, and it has no edge.**
   Under a desk-faithful mechanisation it fires **91 times** (1 per 18 bars) for a mean of
   **−0.113R** at 36.3% win, against a matched placebo of −0.020R (−0.75 placebo-sd).
   Remove the two desk trades and the remaining 89 average **−0.160R**; the remaining 32
   *shorts* average **−0.273R** at 25% win. The desk's two winners are 2 of 34 Tier-B shorts
   and 2 of 19 target-hits. **The two wins are not evidence of an edge in this shape.**
3. **Three zero-volume bars inside RTH — all three are inside the merge** (bars 1151, 1154,
   1157 = 12/17 09:00, 12:00, 15:00 ET). There is **no** zero-volume RTH bar anywhere else
   in the tape. NOTES.md line 630 says "the 4 zero-volume RTH bars"; the correct count is
   **3**, and NOTES' own table at line ~605 already lists three. Minor, but it is a number
   quoted in a defect write-up.
4. **The desk's zero-volume story is right on the rate and wrong on the mechanism.** 60 of
   1,635 bars (3.67%) carry v=0, which matches the audit's 3.5–4.0%. But **56 of those 60
   are the 18:00 ET bar** — 78.9% of every 18:00 bar in the tape. Every other overnight hour
   (00:00–08:00, 19:00–23:00) has **zero or one**. It is not "the thin overnight hour"; it is
   one hour, the first hour after the 17:00–18:00 maintenance halt, where the volume field is
   systematically unpopulated. Further: **all 60 zero-volume bars have a non-zero range**
   (min 3.00, median 8.00, max 93.25 pts). A bar cannot print an 8-point range on zero
   trades, so these are *missing-volume-field* bars, not idle-market bars.

---

## 1. Independent sweep for a second roll merge

### Method (deliberately not `roll_flags()`)

`view.py`'s detector tests **envelope constancy** (high-band and low-band spread small
relative to mean bar range) plus a **max-jump** gate. It has two tuned constants
(`band_frac`, `min_range`), one more (`jump_frac`) added after a second false positive, and
one fixed implementation bug — all against a single positive example. I did not re-use it as
the finder.

My test is a different arithmetic property, the **straddled forbidden corridor**:

> In a window of *W* bars, find the widest price band that (a) **no** open/high/low/close
> touches, and (b) **every** bar in the window straddles — low below it, high above it.

Both at once is impossible for a single instrument: a bar whose low is under a band and whose
high is over it traded *through* the band, so some quote must land inside. Two contract months
interleaved at a constant calendar spread satisfy both trivially — the spread is the corridor
and every bar spans both legs. A large directional move or a weekend gap also creates an
untouched band, but it is **not straddled** (bars sit wholly above or wholly below it), so
condition (b) is the whole discriminator and it needs no tuned fraction. Reported as points
and as a multiple of the prior 20-bar median range.

Swept: every window width 3–25 at every start (1,635 starts × 23 widths).

### Result

| | |
|---|---|
| regions with corridor ≥ 20 pt and ≥ 2.0× prior median range | **1** |
| that region | **bars 1146–1158**, 2024-12-17 04:00 → 16:00 ET, n=13 |
| widest straddled corridor there | **71.75 pt** (W=3), **55.00 pt** at the full W=13, **10.6×** prior median range |
| corridor band | 6064.75 – 6136.50, untouched by any of 52 OHLC values, straddled by all 13 bars |
| corroborating descriptors | mean range 84.23, high-band 13.50, low-band 20.75, max \|o[i]−c[i−1]\| 74.50, 3 zero-volume bars |

The detector recovers the run's **length** on its own: at W=13 the corridor is 55.00 pt, and
at W=14 it collapses to 6.75 pt. The merge is exactly 13 bars and cleanly bounded.

**With bars 1140–1165 excised, the best straddled corridor anywhere else on the tape:**

| width | widest corridor elsewhere | ×prior median range | where |
|---|---|---|---|
| W=3 | 19.75 pt | 1.82 | 1488–1490, 2025-01-10 10:00 |
| W=4 | 14.75 pt | 1.76 | 1445–1448, 2025-01-08 06:00 |
| W=7 | 10.25 pt | 1.22 | 1445–1451 |
| W=13 | **0.50 pt** | 0.06 | 548–560 |
| W≥16 | **0.00 pt** | 0.00 | — |

The merge sits at 55–71.75 pt; the best non-merge candidate on the entire tape is 19.75 pt at
W=3 and effectively nothing past W=8. **This is not a marginal call.** I inspected 1486–1492,
1444–1451 and 725–729 by eye: each is an ordinary volatile RTH sequence with textbook
continuity (every open within 0.5 pt of the prior close) and normal volume.

### Reconciliation with `roll_flags()`

- Run on the current 1,635-bar tape, `roll_flags()` reports **1** suspect run: 1146–1158,
  mean range 84.23, high-band 13.5, low-band 20.75, max-jump 74.5. **We agree exactly, on
  both endpoints.**
- My method finds **nothing** that `roll_flags()` misses.
- My method **correctly rejects both of `roll_flags()`'s documented historical false
  positives without needing the jump test**: bars 1081–1086 are never flagged at all, and
  1445–1448 reach only 14.75 pt / 1.76× — under threshold. The straddle condition does for
  free what the `jump_frac` gate was added to do. That is a suggestion, not a demand: the
  desk's detector has three tuned constants where the corridor test has a structural
  impossibility, and one of those constants exists only to kill 1446–1449.
- **Caveat that applies to my method too:** there is one positive example in this tape.
  My thresholds were not fitted to it (the 3× separation would survive almost any choice),
  but "validated on n=1" is still the honest description.

### Calendar

| | |
|---|---|
| tape span | 2024-10-06 → 2025-01-21, 89 ET dates, 1,635 bars |
| Dec-2024 quarterly expiry (~12/20) | **inside** the tape — the merge sits 3 sessions before it, as expected |
| Mar-2025 quarterly expiry (~03/21) | **outside** the tape — **not testable**, and no partial signature near the end either (widest straddled corridor over bars 1590–1634 is 5.50 pt) |

**Absence stated precisely: across all 1,635 bars and all window widths 3–25, exactly one
straddled forbidden corridor exists, at bars 1146–1158. There is no second merge on this
tape, and the tape does not reach the next quarterly roll.**

### Orthogonal corroboration

A third, cheap descriptor — wide bars (range ≥ 3× prior median and ≥ 25 pt) whose open *and*
close both sit outside the middle 60% of the bar, i.e. bars whose interior is never visited —
gives 46 such bars, with only three runs of ≥3 consecutive: **(1146–1155)**, (726–728) and
(1179–1181). The latter two are the volatile-but-continuous sequences already inspected and
the ones NOTES.md burst 6 uses as its own control. Same answer from a third direction.

---

## 2. Regime classification

Stated definition, no tuning:

- `ATR14(i)` = mean true range over bars *i*−13…*i*.
- **vol** = percentile rank of `ATR14(i)` within the trailing **250** ATR14 values.
  `LO` < 33, `MID` 33–67, `HI` > 67.
- **trend** = `(c[i] − c[i−40]) / ATR14(i)`. `DOWN` < −1.5, `FLAT` −1.5…+1.5, `UP` > +1.5.
- Bars without 250 bars of ATR history are `WARMUP` and excluded: **263 bars** (bars 0–262,
  through 2024-10-22 04:00 ET). **1,372 bars graded.**

### Grid (share of the 1,372 graded bars)

| vol | DOWN | FLAT | UP | row |
|---|---|---|---|---|
| **LO** | 114 (8.3%) | 68 (5.0%) | 281 (20.5%) | 463 (33.7%) |
| **MID** | 141 (10.3%) | 92 (6.7%) | 172 (12.5%) | 405 (29.5%) |
| **HI** | 222 (16.2%) | 141 (10.3%) | 141 (10.3%) | 504 (36.7%) |
| **col** | 477 (34.8%) | 301 (21.9%) | 594 (43.3%) | 1,372 |

Two structural facts worth carrying:

- **The tape is directional 79% of the time** by this measure (43.3% UP + 34.8% DOWN); only
  21.9% is FLAT. A 40-bar / 1.5-ATR threshold is generous, but the reading is that flat
  balance is the *minority* state here, which is the opposite of the desk's working
  assumption in several NO_TRADE notes ("mid-range, no edge").
- **Volatility and direction are coupled asymmetrically.** `LO/UP` is the single largest cell
  (20.5%) and `HI/DOWN` the second (16.2%): the tape grinds up quietly and falls loudly.
  `LO/DOWN` is only 8.3%.

### Distribution over calendar time (by ET week, dominant cells)

| week of | n | dominant | 2nd | 3rd |
|---|---|---|---|---|
| 2024-10-21 | 87 | HI/DOWN 33% | MID/DOWN 16% | HI/FLAT 15% |
| 2024-10-28 | 115 | HI/DOWN 34% | HI/FLAT 18% | MID/FLAT 16% |
| 2024-11-04 | 115 | HI/UP 29% | LO/UP 28% | MID/UP 17% |
| 2024-11-11 | 115 | LO/UP 23% | MID/DOWN 20% | HI/DOWN 17% |
| 2024-11-18 | 115 | HI/FLAT 35% | HI/UP 19% | MID/DOWN 13% |
| 2024-11-25 | 79 | **LO/UP 65%** | MID/UP 13% | LO/FLAT 11% |
| 2024-12-02 | 115 | **LO/UP 65%** | LO/FLAT 15% | MID/FLAT 15% |
| 2024-12-09 | 115 | LO/DOWN 23% | HI/DOWN 16% | MID/DOWN 13% |
| 2024-12-16 | 115 | HI/DOWN 37% | HI/UP 25% | HI/FLAT 18% |
| 2024-12-23 | 73 | MID/UP 49% | HI/UP 22% | LO/UP 11% |
| 2024-12-30 | 86 | MID/DOWN 33% | HI/DOWN 20% | HI/FLAT 15% |
| 2025-01-06 | 108 | HI/DOWN 28% | LO/DOWN 23% | LO/UP 19% |
| 2025-01-13 | 115 | MID/UP 28% | LO/UP 27% | HI/UP 13% |
| 2025-01-20 | 19 | LO/UP 58% | MID/UP 42% | — |

The regimes are **strongly autocorrelated at the week scale** — most weeks have one cell
taking a third or more, and the Thanksgiving-to-early-December stretch is 65% `LO/UP` two
weeks running. That matters for any statistic computed across this tape: effective sample
size in regime terms is closer to **14 weeks** than to 1,372 bars.

Note the week of 2024-12-16 reads `HI/DOWN 37%` / `HI/UP 25%` — that is partly the merge
inflating ATR14 for ~14 bars either side, exactly as NOTES burst 6 predicted. Regime labels
for bars ~1132–1172 should be treated as poisoned, not as data.

---

## 3. The pattern: where else does it fire, and does it pay?

### Mechanisation

The desk has never written a machine-readable spec for thesis 5, so I reconstructed it from
the two callouts' own wording. Two tiers, both stated:

**Tier A — the bare shape.** At bar *i*: a confirmed fractal pivot (k=3, a pivot at *j* is
usable only from *j*+3, lookback 300 bars) at price *L*; *L* was **broken** — some bar *b* in
(*i*−24, *i*) closed beyond *L* by > 0.25·ATR14; and bar *i* **retests and rejects** it:
for a broken pivot low, `h[i] ≥ L` and `c[i] < L` (short); mirrored for a broken pivot high
(long). Entry next bar's open ∓1 tick, stop at bar *i*'s opposite extreme ±1 tick, target
2.0R, engine rules from `missed.py` (stop wins a same-bar tie, flat at the 16:00 ET bar).
Desk filters applied: stop ≥ 0.50·ATR14, no fill landing on a 15:00 or 16:00 ET bar, nothing
inside the merge.

**Tier B — desk-faithful.** Tier A plus the three preconditions both callouts actually cite:
(a) direction agrees with the 40-bar trend (SHORT only in `DOWN`, LONG only in `UP`) — both
trades lead on "lower highs and lower lows"; (b) **first** retest per break episode only
(level+side de-duplicated for 48 bars), so one shelf cannot contribute seven signals;
(c) the break must be within 12 bars, so the level is still live.

**Both tiers keep both real trades.** My scanner independently finds bar 452 at level 5801.0
and bar 1337 at level 5982.75 — the desk's own levels, not approximations.

### Counts

| | Tier A | Tier B |
|---|---|---|
| raw signal bars (bar, side unique) | 812 | — |
| rejected by desk rules | 370 (296 sub-floor stop, 92 forbidden window, 16 in merge) | — |
| **tradeable signals** | **442** | **91** |
| frequency | 1 per **3.7** bars | 1 per **18.0** bars |
| side mix | 261 LONG / 181 SHORT | 57 LONG / 34 SHORT |

**The pattern is not rare. It is available roughly once a session under the strict reading and
several times a session under the loose one.** The desk has fired on it twice in 1,635 bars.

### Outcomes

| set | n | mean | median | win | sum | targets |
|---|---|---|---|---|---|---|
| Tier A all | 442 | **+0.023R** | −1.000 | 38.0% | +9.98R | 117 |
| Tier A short | 181 | +0.071R | −1.000 | 38.1% | +12.83R | 54 |
| Tier A long | 261 | −0.011R | −1.000 | 37.9% | −2.85R | 63 |
| **Tier B all** | **91** | **−0.113R** | −1.000 | 36.3% | −10.28R | 19 |
| Tier B short | 34 | −0.139R | −1.000 | 29.4% | −4.72R | 8 |
| Tier B long | 57 | −0.098R | −1.000 | 40.4% | −5.56R | 11 |
| **Tier B minus the 2 desk trades** | **89** | **−0.160R** | −1.000 | 34.8% | −14.28R | 17 |
| **…shorts only** | **32** | **−0.273R** | −1.000 | **25.0%** | −8.72R | 6 |

### Placebo control

Same engine, same stop sizes, same side mix, **random entry bars**, 40 trials:

| | real mean | placebo mean | difference | in placebo-sd |
|---|---|---|---|---|
| Tier A (n=442) | +0.023R | −0.013R | +0.035R | **+0.70** |
| Tier B (n=91) | −0.113R | −0.020R | −0.092R | **−0.75** |

**Neither tier is distinguishable from an arbitrary bar.** Tier B is nominally *worse* than
random. This is the same result the desk already found for FVGs and order blocks (BRIEF.md
rule 8), now for its own live pattern.

### By regime — and the two real trades

**Regime at the two trades:**

| trade | bar | ET | level | regime | ATR14 | ATR pct | 40-bar change |
|---|---|---|---|---|---|---|---|
| #1 entry 5791.75 | 452 (rejection) | 2024-11-01 10:00 | 5801.00 | **MID/DOWN** | 11.20 | 63.2 | −53.25 = −4.76 ATR |
| #2 entry 5973.25 | 1337 (rejection) | 2024-12-31 07:00 | 5982.75 | **LO/DOWN** | 9.66 | 26.0 | −43.75 = −4.53 ATR |
| #2 as decided | 1339 | 2024-12-31 09:00 | — | **LO/DOWN** | 10.62 | 32.4 | −54.75 = −5.15 ATR |

Both are **DOWN-trend, non-high-volatility** — and both at a trend magnitude of about
−4.6 ATR over 40 bars, roughly 3× the DOWN threshold. That is the one thing the two trades
share that most of the 91 candidates do not.

**Tier B by cell** (FLAT cells are empty by construction — the trend-alignment filter):

| cell | n | mean | win | density (per 100 bars in cell) | Tier A n |
|---|---|---|---|---|---|
| LO/DOWN | 13 | **+0.154R** | 38.5% | 11.40 | 66 |
| LO/UP | 31 | −0.208R | 32.3% | 11.03 | 79 |
| MID/DOWN | 16 | **−0.108R** | 31.2% | 11.35 | 52 |
| MID/UP | 16 | +0.139R | 56.2% | 9.30 | 59 |
| HI/DOWN | 5 | **−1.000R** | **0.0%** | 2.25 | 31 |
| HI/UP | 10 | −0.134R | 40.0% | 7.09 | 32 |

Side-matched in the two trades' own cells:

| cell, SHORT only | Tier A | Tier B |
|---|---|---|
| MID/DOWN (trade #1) | n=26, mean −0.265R, win 27% | n=16, mean −0.108R, win 31% |
| LO/DOWN (trade #2) | n=33, mean +0.030R, win 33% | n=13, mean +0.154R, win 38% |

**Read that plainly. Trade #1's cell is the worst short cell on the tape apart from high-vol;
trade #2's cell is the only one that is even nominally positive, on n=13.** The desk did not
catch two instances of a rare edge. It caught 2 of 34 trend-aligned short firings, both of
which happened to be among the 8 that reached target.

**Where the pattern is actively dangerous:** `HI/DOWN`. Tier A shorts there are **n=11, mean
−0.729R, win 9.1%, zero targets**; Tier B is **0 for 5, −1.00R each**. High-volatility
downtrends are 16.2% of the graded tape and 37% of the week of 2024-12-16. Whatever the desk
does next, "failed retest, short, high-vol downtrend" is the one combination the tape says to
avoid outright — and note that this is also the cell the merge inflates, so some of those
bars are reading a calendar spread.

**Density** is roughly flat at 9–11 Tier-B signals per 100 bars across `LO/DOWN`, `LO/UP`,
`MID/DOWN`, `MID/UP`, and drops to 2.25 in `HI/DOWN`. So the answer to the framing question:
**the pattern is common in almost every regime, with no cell where it is both frequent and
profitable.** It is scarce only in exactly the regime where it also loses hardest.

---

## 4. Volume and bar-shape sanity

### Integrity counts (whole tape, 1,635 bars)

| check | count |
|---|---|
| OHLC ordering violations (`l ≤ o,c ≤ h`) | **0** |
| rangeless bars (`h == l`) | **0** |
| duplicate timestamps | **0** |
| non-monotonic timestamps | **0** |
| negative volume | **0** |
| prices off the 0.25 tick grid | **0** |
| zero-volume bars | **60 (3.67%)** |

89 ET dates. Bars-per-date: 54 dates with the full 23, 15 with 17 (Fridays, no 18:00–23:00),
15 with 6 (Sundays, 18:00–23:00 only), and 5 partial dates (19, 16, 5, 4, 4 bars — the tape's
first and last dates plus the 11/29, 12/24 and 1/20 half sessions). 19 dates have no 16:00
bar. Nothing anomalous in the session skeleton.

### Rate per ET hour

| ET hour | bars | rangeless | zero-vol | mean volume | RTH |
|---|---|---|---|---|---|
| 00:00 | 71 | 0 | 0 (0.0%) | 4,007 | |
| 01:00 | 71 | 0 | 0 (0.0%) | 5,019 | |
| 02:00 | 71 | 0 | 0 (0.0%) | 7,600 | |
| 03:00 | 71 | 0 | 0 (0.0%) | 12,815 | |
| 04:00 | 71 | 0 | 0 (0.0%) | 12,206 | |
| 05:00 | 71 | 0 | 0 (0.0%) | 8,790 | |
| 06:00 | 71 | 0 | 0 (0.0%) | 10,440 | |
| 07:00 | 71 | 0 | 0 (0.0%) | 13,828 | |
| 08:00 | 71 | 0 | 0 (0.0%) | 26,875 | |
| 09:00 | 73 | 0 | **1 (1.4%)** | 119,764 | RTH |
| 10:00 | 72 | 0 | 0 (0.0%) | 162,975 | RTH |
| 11:00 | 72 | 0 | 0 (0.0%) | 103,140 | RTH |
| 12:00 | 72 | 0 | **1 (1.4%)** | 78,901 | RTH |
| 13:00 | 70 | 0 | 0 (0.0%) | 75,363 | RTH |
| 14:00 | 70 | 0 | 0 (0.0%) | 73,862 | RTH |
| 15:00 | 70 | 0 | **1 (1.4%)** | 99,855 | RTH |
| 16:00 | 70 | 0 | 0 (0.0%) | 28,700 | RTH |
| **18:00** | 71 | 0 | **56 (78.9%)** | 2,631 | |
| 19:00 | 72 | 0 | 1 (1.4%) | 7,158 | |
| 20:00 | 71 | 0 | 0 (0.0%) | 7,235 | |
| 21:00 | 71 | 0 | 0 (0.0%) | 5,857 | |
| 22:00 | 71 | 0 | 0 (0.0%) | 5,328 | |
| 23:00 | 71 | 0 | 0 (0.0%) | 3,863 | |

All 60 zero-volume bars are accounted for: **56** at 18:00 ET, **3** inside the merge
(09:00, 12:00, 15:00 on 12/17), **1** at 19:00 — bar 0, the first bar of the tape, which is
a truncated leading bar and not a defect of the series.

### Zero-volume bars inside RTH (09:00–16:00 ET) — not benign

    [1151] 2024-12-17T09:00  o 6131.50  h 6135.00  l 6047.25  c 6055.00   range 87.75
    [1154] 2024-12-17T12:00  o 6061.25  h 6136.25  l 6054.25  c 6059.75   range 82.00
    [1157] 2024-12-17T15:00  o 6119.75  h 6133.25  l 6040.00  c 6054.00   range 93.25

**All three sit inside bars 1146–1158.** So the only non-benign zero-volume bars on the tape
are inside the region already quarantined, and they are a *fourth* independent signature of
the merge (after envelope constancy, forbidden corridor, and hollow-bar runs). There is **no
RTH zero-volume bar anywhere else in 1,635 bars.**

### The finding the audit's 3.5–4% rate hides

Two things the aggregate rate conceals, both of which the desk is currently reasoning from:

1. **It is one hour, not "overnight".** 93% of the zero-volume bars are the 18:00 ET bar and
   they are 79% of that hour. The 00:00–08:00 and 20:00–23:00 hours, which the desk keeps
   describing as "the thin overnight hour", have **zero** between them. The 18:00 bar is the
   first hour after the 17:00–18:00 maintenance halt, which is exactly where a feed would be
   expected to drop a volume field.
2. **Zero volume with a real range is internally inconsistent.** Every one of the 60 has
   `h > l` — minimum range 3.00, median 8.00 points. Price cannot move 8 points on zero
   trades. These are bars with a **missing volume field**, not bars with no activity. Their
   prices look usable and their volumes are not.

Consequence for the desk's own process, since it turns up repeatedly in `callouts.jsonl`:
several NO_TRADE decisions decline a bar on "2–10k volume". At 18:00 ET the volume number is
absent rather than small, so that filter is rejecting 56 bars for a reason that is not in the
data. If a 18:00 decision ever matters, the honest statement is "volume unknown", not
"volume thin".

---

## 5. What I could not determine

- **Whether a March-2025 roll is corrupted.** The tape ends 2025-01-21, two months before the
  expiry. Not testable from `visible.jsonl`, and no partial signature appears near the end
  (the widest straddled corridor over bars 1590–1634 is 5.50 pt).
- **Whether the merge signature generalises.** One positive example exists in this tape.
  My corridor test was not fitted to it and separates it from the next-best candidate by ~3×,
  but "validated on n=1" is the accurate description of my method as much as of
  `roll_flags()`. The other eight rolls the desk expects on the full span, and any MNQ/MGC/MCL
  equivalent, are outside my lane.
- **Whether the desk's discretion adds the edge the mechanical shape lacks.** n=2 against 91
  candidates cannot answer this. What I can say is that the *shape* has no edge and slightly
  negative expectancy, so any edge must live entirely in the discretionary filters the desk
  applied — and the only measurable thing the two trades share that the cohort does not is a
  trend magnitude near −4.6 ATR over 40 bars, which is a single observation dressed as a
  hypothesis. It should be pre-registered and tested forward, not fitted here.
- **The exact spec of thesis 5.** No machine-readable definition exists, so Tier A and Tier B
  are my reconstructions. The counts are sensitive to K=3 pivots, the 0.25-ATR break
  threshold, the 12-bar recency window and the 48-bar de-duplication. The *sign* and the
  placebo comparison are robust to plausible variation; the exact 91 is not.
- **Regime labels near the merge.** Bars ~1132–1172 have ATR14 poisoned by the calendar
  spread, so their vol percentile (and hence cell) is not meaningful. I have left them in the
  census rather than silently dropping them, and flagged them here instead.
- **Placebo completeness.** The control matches side and stop size but not hour-of-day or
  regime, so it is a drift control, not a full one. A regime-matched placebo would be a
  stronger test and is cheap to add.

---

## Reproduce

    python3 agents/C_shape.py     # integrity, hour-of-day, zero-volume
    python3 agents/C_merge.py     # independent merge sweep + calendar coverage
    python3 agents/C_regime.py    # regime census, pattern sweep (Tier A/B), placebo

All three read only `../visible.jsonl`. `C_regime.py` also reports the two desk trades'
regimes; it does not read `callouts.jsonl` (the two bar indices are hard-coded from the
callout records quoted above).

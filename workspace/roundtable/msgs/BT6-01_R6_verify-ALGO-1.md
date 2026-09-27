RE:    BT6-ALGO-1
ALSO:  R6-D1, D45, D49, D40, D48, D28, R4-M3, R6-M1, R6-M2, BT6-REQ-1, BT6-REQ-2, BT6-REQ-3
FROM:  BT6
TO:    R6
TASK:  BT6 burst 01-02 — making R6-D1 executable

# Is my reading of R6-D1 faithful? All ten of your figures reproduced; four things I found beyond them

Your audit is at `research/R6_report_audit.md`; R6-D1 is §1 "My own measurements",
lines 120–156. I read it, wrote my own census from the primitives, and measured
before looking for anything new — your own method note (§8, the chronology
winners) is why. **I did not read or run your script; it is not in the tree.**

Verdict request is on my *reading* and my *silent choices*, not on a divergence:
I found nothing in R6-D1 to disagree with.

---

## 1. Every published R6-D1 figure reproduces to the printed digit

`[measured: PYTHONPATH=. python3 workspace/roundtable/backtest/BT6/code/vwap_daily_census.py
→ backtest/BT6/out/vwap_daily_census.json]`

Band-1 half-width `< 1 tick`:

| cell | mine | yours |
|---|---|---|
| MGC / MES / MNQ / MCL **60m** | 7.5% / 8.4% / 7.5% / 8.9% | 7.5% / 8.4% / 7.5% / 8.9% |
| MGC / MES / MNQ / MCL **240m** | 20.0% / 20.5% / 19.8% / 21.8% | 20.0% / 20.5% / 19.8% / 21.8% |
| **MGC 1440m** | **2511 / 2511** | 2511 / 2511 |
| **MES 1440m** | **1859 / 1859** | 1859 / 1859 |

Condition census on `[1440, 7200]`:

| condition | MGC mine / yours | MES mine / yours |
|---|---|---|
| `above_vwap` | 2319 = 92.4% / 92.4% | 1854 = 99.7% / 99.7% |
| `vwap_band_extension` | 2506 = 99.8% / 99.8% | 1859 = 100.0% / 100.0% |
| `vwap_band1_bounce` | **0** / 0 | **0** / 0 |
| `vwap_reclaim` | 1691 = 67.3% / 67.3% | 1459 = 78.5% / 78.5% |
| `vwap_proximity` | 2418 = 96.3% / 96.3% | 1790 = 96.3% / 96.3% |
| `above_vwap` dir == `candle_close_strength` dir | **1092 / 1092** / 1092/1092 | **919 / 919** / 919/919 |

Two extensions of your own cells, same direction: **MNQ 1440m** is 1859/1859
sub-tick, `above_vwap` 99.9%, `vwap_band1_bounce` 0, agreement **939/939**; and
all three replicate on `data/archive` daily (MGC 4008/4008, MES 1863/1863,
MNQ 1863/1863).

## 2. `D45`'s zero-σ-on-the-first-bar is the mechanism — confirmed, exactly

I cross-tabulated `half-width < 1 tick` against "`vwap_bands`' own anchor key
changed at this bar", computing the key the way the indicator does
(`trading_day(bar.ts)`, `volume.py:34-35`), not off a clock.

**`first-of-day AND NOT sub-tick` is 0 in every cell, every symbol, every
timeframe** — 60m, 240m and 1440m, MGC/MES/MNQ/MCL. And at 1440m
`distinct_trading_days == bars` and `not_first_of_day == 0`. So the 100% is not an
empirical rate; it is the one-bar case of `D45` holding by construction.

One refinement `D45` does not carry: at 60m, **40–46% of sub-tick bars are NOT
first-of-day** (150/376 MGC, 195/422 MES, 204/445 MCL) — R1's σ ramp still under
a tick on bar 1 and sometimes bar 2. At 240m that is 2/269 on MGC and 0/267 on
MNQ. So "zero on bar 0, sub-tick for one-to-two bars, and at 1440m there is no
bar 1" — the 100% is a **limit**, reached because the series has no later bars,
not because the ramp got worse.

---

# Where I had to choose — the field you need to answer

Each of these could have moved a number, and R6-D1 is silent on all of them.
Full table with the rejected alternative in `backtest/BT6/ALGOS.md`.

**Q1 — what I counted as a tick.** `config.get_contract(sym).tick_size`: MGC 0.10,
MES/MNQ 0.25, MCL 0.01. **Not** the minimum observed price increment in the file —
on MGC's float32-ish daily closes that is ~1e-6 and would have reported 0%
sub-tick everywhere. Is the contract tick what you used? *(Your 60m/240m numbers
match mine exactly, which is strong evidence yes, but I would rather have it
said.)*

**Q2 — how I treated the first bar.** I dropped **no** warm-up. Bar 0 of each
file is in the sample. Bars whose band is `None` are excluded from the
denominator and counted separately — there are **0** in every cell, which is the
absent guard, measured. Dropping bar 0 would remove one collapsed bar per session
and would be smuggling in the fix whose absence is the finding.

**Q3 — which timeframes I called "daily".** `minutes == 1440` only: the
`csv/raw/*_1d.csv` files and `data/archive/*_1440m.jsonl`. I deliberately did
**not** count 7200 as a second daily timeframe even though `R4-M3` shows
`align_bucket` makes it one, so R6-D1 stays disentangled from BT4's finding. Do
you intend R6-D1 to cover 7200 as well? If you do, the daily counts double and the
overlap with `R4-M3` needs a sentence.

**Q4 — half-width, and which side.** `upper_1 − vwap`, with the symmetry against
`vwap − lower_1` asserted per bar (max asymmetry 0.0 in every cell). Strict `<`
for "under a tick", matching your wording; I also carry `<= 1 tick`, `< 0.5 tick`
and `== 0.0` so the threshold can be moved. At 1440m every threshold gives 100%.

**Q5 — which store.** `csv/raw` primary, because it is what every published row
was measured on. `data/archive` daily as an independent replication, per
`BRIEF.md`'s ruling — and I verified the two rather than assuming, because that
policy's own condition 2 says the 60m agreement does not generalise. `MCL_1440m`
excluded: one row is not data.

**Q6 — "how many results".** I answered it **twice**, because the two differ ~50×:
**196 distinct stored strategy ids** at tf=1440 (505 raw rows, but every row is
also in its store's `all_rows.json`), and **23,309 evaluated strategies** in the
three daily chronology ledgers. Which of those did you mean when you wrote that
`D45`'s statement understates the harm?

---

# Four things I found that R6-D1 does not state

Offered as candidate strengthenings. Each could equally mean I have read you too
broadly, which is why they are here and not in a report.

**(a) At 1440m the group's three SIGNALs are two statements, one the negation of
the other.** `[measured: pairwise direction agreement over co-firings]`

| pair | MGC | MES |
|---|---|---|
| `above_vwap` × `vwap_reclaim` | 1689/1689 = 100% | 1455/1455 = 100% |
| `above_vwap` × `candle_close_strength` | 1092/1092 = 100% | 919/919 = 100% |
| `above_vwap` × `delta_confirms_bar` | 1829/1829 = 100% | 1602/1602 = 100% |
| `vwap_reclaim` × `delta_confirms_bar` | 1678/1678 = 100% | 1450/1450 = 100% |
| **`above_vwap` × `vwap_band_extension`** | **0/2319 = 0%** | **0/1854 = 0%** |

So your `above_vwap ≡ candle_close_strength` observation extends to **four
conditions in three groups** (`vwap`, `candlestick`, `orderflow`), which is R1's
finding C-1 at 1440m, and `vwap_band_extension` is their exact negation because
`close >= vwap_u2` is tested before `close <= vwap_l2`.

*The conservative half, which I want on the record:* `GLOBAL_EXCLUSIVE`
(`combinator.py:391-402`) does not contain any of these pairs, so a daily VWAP
strategy drawing `above_vwap` + `delta_confirms_bar` counts one observation twice
— but **the opposite-sign pair cannot be generated.** The combinator draws at most
one condition per group (`combinator.py:538-541`) and no template lists `vwap` in
both required and optional. So **no published null is a "two vwap signals
cancelled" artefact.** That is a thing R6-D1 could have been read as implying and
does not.

**(b) `above_vwap`'s 92.4% on MGC is not selectivity — it is MGC's flat bars.**
`csv/raw/MGC_1d.csv` carries **281 bars with `high == low`** (11.2% of 2511)
against **1 of 1859** on MES and MNQ. On MGC daily bars with any range,
`above_vwap` fires **2228 / 2230 = 99.91%**; on MES, 1854/1858 = 99.78%. That
makes your "the fix is void at 1440m" *stronger*: the docstring records the
pre-fix `close != vwap` version as firing on "99.99% of bars"
(`library.py:296-305`) and the fixed version is back to 99.9%. **92.4% understates
it, and the shortfall is a property of MGC's daily file rather than of the
condition.** Do you want A16 restated with the conditional rate?

**(c) 91 of those 281 rangeless bars still emit a direction — 41 LONG, 50 SHORT.**
The largest `|close − vwap|` among them is **9.1e-13 price units**. `typical =
(high+low+close)/3` does not round-trip to `close` in binary floating point even
when `high == low == close`. On a bar with **no range at all**, `above_vwap`
returns a direction decided by the last bit of a float. I would describe that as
noise wearing a direction rather than as a degenerate signal, and it is not in
R6-D1.

**(d) `vwap_band1_bounce` is `VOID`, and I confirmed it through the engine rather
than by arithmetic.** 731 / 730 / 665 generated MGC / MES / MNQ daily strategies
carry it — **2,126 of 23,309 (9.1%)** of every daily population this programme has
generated — and all 2,126 take **0 trades** through `run_portfolio` on `csv/raw`
daily bars. The control in the same run: the `above_vwap` arm took 11,014 trades
on the same bars with the same exits, so the zero is the condition and not a
broken harness. **That is a sixth structurally zero-trade configuration**, to sit
beside R1's five, and the largest of them at daily frequency.

---

# One friendly correction, to R1's wording rather than to yours

R1 wrote that σ is "**exactly** zero on the first bar of every CME trading day,
by construction" (`msgs/04_R1_R3_re-VWAP-BAND.md:108-115`). Algebraically yes.
Numerically no: `var = max(0.0, pv2/vol − mean²)` cancels two quantities near
1.8e6 on MGC, so `sd` lands near **1e-5 price units**. The half-width is exactly
`0.0` on **2300/2511 MGC, 1776/1859 MES and 1765/1859 MNQ** daily bars — so an
assertion written `sd == 0.0` fails on roughly one daily bar in twelve.

Nothing in R6-D1 changes (1e-5 on a 0.10 tick is not a band). It does change how
the regression test may be written, and `tests/test_bt6_vwap_daily.py` asserts
against the tick, never against zero, with one hand-picked counter-example bar
pinning why.

---

# Two things I am reporting to the manager, not to you

- **`BT6-REQ-2`** — `data/archive/MGC_1440m.jsonl` has a **10× scale break at
  index 384**: `2012-04-25 c=164.10` → `2012-04-27 c=1664.80`. Bars 0–383 sit at
  131.70–188.90, the rest at 1050.80–5318.40; 551 of 4008 bars have `high == low`
  and 355 have `volume == 0`. It does not touch R6-D1 — the collapse is a
  within-bar property and reproduces identically on both sides of the break — but
  it is `D40` wearing a new instrument on the store `DISC2`'s 25-year proposal
  depends on.
- **`BT6-REQ-1`** — the warm-up guard, with the radius attached. I did **not**
  patch `futures_agents/`: the patch is three lines and the consequence is that
  every daily VWAP strategy takes zero trades, which is a deletion of published
  rows and therefore a board decision.

---

# And your `require_alignment` item: verified harmless, and sized

You asked whether "harmless in every published cell" holds. **It does**, and I
checked it rather than inheriting it. `alignment(from_tf)` skips `tf < from_tf`
(`features.py:742-750`) and `passes` is called with `self.primary_tf`
(`base.py:660`), so the no-arg call is correct iff `primary_tf == min(frame)`.

`[measured: alignment() vs alignment(primary_tf) on every snapshot]` — identical
on **1347/1347** MES 240m `[240,1440]`, **1348/1348** MGC 240m, **5000/5000** MES
60m `[60,240,1440]`, **1859/1859** MES 1440m `[1440,7200]`. **9,554 of 9,554.
Report D's `require_alignment ≥ 0.5` on MES 240m survives.** Both studies that set
the field (`w2/mtf2.py:80`, `w2/mtf3.py:61`) draw from `w2rank.population`, which
filters `x.primary_tf == tf` (`w2rank.py:69-71`), so the precondition holds by
construction.

And the hazard is worth a number, because the reason it is harmless is a
coincidence of `FRAMES` rather than a design. On a 60m base with frame
`[60,240,1440]` and `primary_tf = 240`, `alignment()` differs on **84.4% (MES) /
86.5% (MGC)** of bars and the `≥ 0.5` gate **flips verdict on 16.3% / 21.3%**; at
`primary_tf = 1440`, on **33.9% / 39.5%**. So it is not inertness — it is a filter
reading the wrong timeframes, and it lands the moment any anchor/execution study
runs. Filed as `BT6-REQ-3`.

---

## What I need from you

**FAITHFUL** or **DIVERGENT(how)** on my reading, and specifically on Q1–Q6. If
you think (a)–(d) go beyond what R6-D1 claims, say so and I will report them as
BT6 findings under my own id rather than as extensions of yours. If you think any
of them contradicts R6-D1, that is the answer I most want, because your method
note is the reason I replicated before looking.

Until you answer, `BT6-ALGO-1` is `ASKED` and nothing above is a verified number.

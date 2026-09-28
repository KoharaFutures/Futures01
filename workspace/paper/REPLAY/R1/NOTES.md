# REPLAY R1 — MES 60m walk-forward paper. Notes, newest burst at the bottom.

Owner of this directory: agent `REPLAY`. Nothing outside `workspace/paper/REPLAY/**` is written by me.

---

## Burst 1 — bars 0→40. basis `1948339` (2026-09-27)

### Setup

```
init --id R1 --symbol MES --tf 60   ->  11287 bars, 2024-10-06 -> 2026-09-25
next --id R1 --n 40                 ->  cursor 40/11287
```

Read `visible.jsonl` only. Did not open `data/archive/`, `csv/`, `engine.py`, `replay.py`, and did not
inspect `state.json`. The span figures (11,287 bars, 2024-10-06 → 2026-09-25) are quoted from the
harness's own `init` banner, which volunteered them; they say nothing about prices.

**One leak-adjacent thing I absorbed by following the reading order, declared rather than hidden.**
`SERIES_AUDIT.md` §3 contains aggregate statistics for `MES 60m`: 11,286 contiguous-boundary count and
a **mean boundary gap of −0.14 bp**. That is a whole-series aggregate, not a bar-level price, and it
cannot tell me the direction of any particular bar — but it is a fact about the series I am trading
that I learnt outside `visible.jsonl`, and the honest thing is to write it down. It is weakly
*unfavourable* to me if anything: it says MES 60m opens fractionally *below* the prior close on
average, so the fill asymmetry runs mildly against longs and for shorts, by ~1.4 thousandths of a
point. I have not used it and will not size on it. If the account owner wants the reading order
tightened, §3's per-series table is the line to redact.

### What the first 40 bars are

Two 22-hour cycles, 2024-10-06 19:00 ET → 2024-10-08 11:00 ET.

- **Cycle 1 (bars 0–21).** Open 5804.75. Overnight bleed to 5762.5 at 05:00, recovery into the RTH
  open, chop 5769–5788 through the morning. Then **bar 19 (14:00 ET) is the event**: a 39.25-point
  down bar on 152,025 — the widest range and the heaviest volume in the sample — closing 5736.25, two
  ticks off its low. Bar 20 (15:00) bounces to 5755.75, closes 5743.25. Bar 21 is the 16:00 bar and
  the harness flags it `<-- FORBIDDEN WINDOW`.
- **Cycle 2 (bars 22–39).** Opens 5752 and immediately takes out cycle 1's low: **5725.25 against
  5734.0**, then closes back up at 5740.75. Bars 23–31 base in 5736–5754 (and the lows are *not*
  monotonically higher through there — 5744.5, then 5738.25, then 5736.0). From bar 31's 5736.0 the
  lows do climb cleanly for eight bars: 5745.75, 5753.0, 5760.75, 5764.0, 5763.75, 5763.75, 5773.0,
  5782.0. RTH bar 38 (10:00) prints **5795**, the highest since bar 3, on 152,253. Bar 39 (11:00)
  closes 5792.5 on 70,018.

ATR(14) over bars 26–39 ≈ **10.6 points** (range-only, gaps would add a little), so the 0.5-ATR
structural-stop floor of rule 4 is ~5.3 points here, and a $240 permitted risk buys **4 contracts on
an 11-point stop** ($55/contract).

### Decision: NO TRADE at bar 39

Journalled to `NO_TRADE.jsonl`. The reasoning, in the order it actually ran:

The direction of travel is up and I can name it: the 5725.25 sweep failed, and eight consecutive
higher lows carried price 57 points back through the whole of cycle 1's decline. That is the trade a
trend-follower takes and I did not take it, for five reasons that I think are each individually
sufficient:

1. **It is the eighth bar of the run.** 57 points is >5 ATR of travel already spent. Buying here is
   paying for the move I just watched.
2. **Volume halved on the last bar.** 152,253 → 70,018. The thrust was bar 38; bar 39 is a narrower
   continuation on 46% of it. That is the wrong sequence to enter on.
3. **Visible supply is ~2.5 points overhead.** 5795–5808 is where bars 0–3 traded. I have nothing
   above it in view, so a 2R target (~5814 on an 11-point stop) must clear the only shelf I can see,
   inside the four hours left before the 16:00 ET flat.
4. **Rule 1 bites, and against me.** "Higher lows" and "upside break" are not two signals; they are
   *price went up* stated twice. Correlated signals are one signal, and 2-and-a-filter is a ceiling I
   have not reached, not a quota I should fill.
5. **Rule 8 indicts my most persuasive framing.** "Swept the prior low at 5725.25, then reversed" is
   exactly the ICT sweep→shift→retrace sequence, measured in this repo as real, common, and adding
   nothing over its parts. The fact that it is the nicest-sounding sentence available is the reason to
   distrust it.

And a sixth that is about the instrument rather than the chart: **40 bars is under two cycles.** No
lookback longer than ~20 bars is meaningfully estimable, and I have no daily or weekly structure at
all. Everything I just wrote rests on 40 hours of tape. My first few bursts are structurally
under-informed and I would rather say so than dress 40 bars up as a regime read.

**What would have made me trade it:** a pullback holding above bar 38's 5773.0 with the 5795 high
intact — stop under 5770, first target the 5808 shelf, ~1.8R; or a consolidation and then a
break-and-hold above 5795–5808 on *expanding* volume, which would put the entire visible range
behind price.

### Two harness observations (not edits — both are outside what I own)

1. **`replay.py` has no no-trade path.** `journal.jsonl` records orders only, so the default record
   is a record of the trades I liked. `CALLOUT.md`'s paper-mode section says a NO TRADE gets journalled
   with `side: null` and its reason. I did not write into the harness's `journal.jsonl` in case its
   reader is strict; I keep `NO_TRADE.jsonl` beside it in the directory I own, same shape plus
   `bars_visible`. If the owner wants no-trades in the main journal, that is a harness change and it
   is not mine to make.
2. **`alerts.alert()` both prints and returns the rendered card**, so `print(alert(...))` emits it
   twice. Cosmetic; I will bind the result instead of printing it from here on. Not a defect worth a
   `D` number.

### Cadence I propose

**60 bars a burst, one commit per burst, notes before stopping.** 60 bars is ~3 cycles, so a burst
always contains whole 18:00→16:00 sessions rather than cutting one in half, and it is small enough
that I can actually look at every bar instead of skimming. That is ~188 bursts to cross 11,287 bars —
long, and the alternative is looking at bars I have not looked at.

Two adjustments to that default: **I will widen to 100 when flat and the tape is plainly rangebound**
(nothing to decide, and pretending otherwise wastes the turn), and **narrow to 10–20 while a position
is open**, because with a live stop and target the bar-by-bar sequence is the only thing that decides
the fill and I do not want to discover an exit forty bars after it happened.

**`score` deliberately not run yet.** Zero closed trades, so it has nothing to separate from the
placebo, and `--trials` is a count of distinct ideas tried, which is currently 1 (trend-continuation
long on MES 60m) and not worth a threshold test. I will run it at the first double-digit trade count
and report the z against the |z| = 4.5 leak line every time, including when it flatters me.

**Stopped at:** cursor **40/11287**, flat, equity $50,000, drawdown $0, permitted $240 (×1.00).

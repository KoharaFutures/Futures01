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

---

## Burst 2 — bars 40→402. basis `2e7725d` (2026-09-28, autonomous firing)

**Nothing to escalate.** No leak warning (score not due and not meaningful — zero closed trades), no
absorbing state (drawdown $0), no callout-id assertion (9 callouts, 9 unique ids), series not ended.

`REPLAY.md` changed since burst 1: `callouts.jsonl` now carries the `CALLOUT.md` PAPER MODE schema and
the harness owns `entry_price`, `outcome`, `as_of`, `basis` and the whole ladder block. That split is
right and it retires my burst-1 workaround — **`NO_TRADE.jsonl` is superseded** and I have left it in
place as a historical artefact rather than deleting it. Because my cursor had not advanced, I was able
to re-record burst 1's stand-down through the harness at its true `visible_bars` of 40
(`R1-00001-b000040`), so the harness record is complete from bar 39 onward with no backfilled fiction.

### Result: 362 bars, 9 stand-downs, 0 trades, equity $50,000 flat

Roughly **354 bars passed over without a recorded candidate** — overnight chop at 2–10k volume,
mid-range hours, and the 16:00 forbidden bars. The 9 recorded decisions are the bars where I actually
weighed a setup.

### What the tape did, 2024-10-08 → 2024-10-30

- **10/08 → 10/14: a clean one-way uptrend.** 5725.25 → 5918.5, six consecutive higher cycle closes,
  shallow overnight consolidations, expansion concentrated in the 09:00–10:00 ET bars.
- **10/15: the character breaks.** 5918.5 → 5850.0 in one session.
- **10/17 → 10/22: a range, 5865–5927.** 5927 rejected twice (bar 198 printed it and gave back 31
  points on 182k), 5865 bought hard (bar 246 left a 21-point tail on 153k).
- **10/23: the range resolves down.** 5890 → 5801 in five bars, with clean acceptance below 5865.
- **10/24 → 10/30: basing, then compression.** 5801–5893, narrowing to 5837.5–5893.0 over the last
  three sessions. Ends at 5882.25, near the upper edge.

ATR(14) ran 9.2 → 13.7 across the burst; the 0.5-ATR floor of rule 4 therefore sat at 4.6–6.9 points
and repeatedly disqualified the tight structural stops the overnight tape offered.

### The two stand-downs that were right, and the reason they were right

- **Bar 39 (burst 1's long).** Declined as an extended eighth bar into visible supply. **Bar 41's low
  of 5774.5 would have taken out the 11-point stop** from that entry. Stopped out on the second bar.
- **Bar 151 (the failed pre-condition).** At bar 139 I wrote, before seeing the bars, that I would buy
  the 09:00 open only if the overnight held above the prior RTH close. It did not — lower high at
  5916.25 vs 5918.5, drift to 5902.25, 3.75 points below the 5914.0 close. I honoured it. **Bar 153
  then fell to 5877.75 and bar 158 to 5850.0.** A 68-point adverse move avoided by a 3.75-point
  condition I had written down in advance. This is the single strongest argument in the record for
  pre-stating the condition: the miss was small enough that I would certainly have talked my way past
  it after the fact.

### The two things I got wrong, both worth more than the stand-downs

**1. My first pre-stated trigger was badly specified, fired, and would have lost.** At bar 251 I wrote
"SHORT on a break below 5865 with stop above 5882." Bar 263 traded 5863.5 and bar 267 5861.0, so it
fired; the 16.5-point stop would have been hit at bar 271's 5899.25. The defect is exactly what rule 8
names: **I required a tick through the level, not acceptance below it.** A 1.5-point poke through a low
that had just been bought on a 21-point tail is not a break. Revised on record at bar 276: a range-edge
entry needs a full bar to **close** beyond the level and the next bar to **fail to reclaim** it, with
the stop just beyond the extreme of those two bars rather than at a fixed distance.

**2. The revised trigger then fired correctly and I advanced straight past it.** On 10/23 bar 291
closed 5862.25 (below 5865) and bar 292 failed to reclaim, closing 5855.75 on a lower low of 5844.75 —
textbook acceptance. The short was there at bar 293's open of 5856.00, stop just above the 5874.0
two-bar extreme (19.5 points), and bar 294 traded 5815.75 with bar 295 reaching 5801.0. **That is
about 2R and it would have been my first trade and a winner.** I did not decline it; I never saw it,
because at bar 251 I had diagnosed this exact chunk-size flaw, written that I was narrowing to 25 bars,
and then advanced 50 anyway.

**The read was right and the operating discipline was not.** That is the more embarrassing failure and
the one the record needs, because it is not a judgement error I can argue about — it is me not doing
the thing I had just written down. Two turns in a row the pre-statement worked and the execution of my
own cadence rule did not.

### The methodological flaw I named at bar 251, stated plainly

Nine stand-downs and zero trades is **partly a real read and partly an artefact of where I stop**. I
was deciding at whatever bar a 50-bar chunk happened to land on. A randomly chosen bar is usually
mid-structure, so that sampling is biased toward no-trade independently of anything about the market,
and it is how I walked past the 10/23 short. This matters for the eventual placebo comparison: the
placebo gets a decision at whatever bar I recorded one, so **a no-trade bias in my sampling does not
flatter me, it just shrinks the denominator and wastes the exercise.**

Binding from here: **25 bars per advance whenever a pre-stated trigger is live near a level**, 50 only
when price is mid-structure with nothing pending. A trigger is live now, so the next firing opens at 25.

### Pre-stated plan carried into the next firing (written before the bars, as it must be)

The compression is 5837.5–5893.0 inside the defended 5801–5927 range.

- **LONG** if a bar closes above 5893.0 and the next fails to reclaim below it. Stop just under the
  lower of those two bars. First target 5927.
- **SHORT** if a bar closes below 5837.5 and the next fails to reclaim. Stop just above the higher of
  those two bars. First target 5801.

Compression into a defended range is the one structure here where an acceptance break has a real level
to lean on and a real target to pay for it, and it is the setup I most expect to actually take. If I
stand aside on that too, the honest conclusion is that my criteria are unachievable rather than strict,
and I will say so rather than keep collecting stand-downs.

### Distinct theses tried so far: 3

For the eventual `--trials` count, honestly enumerated: (1) trend-continuation long on an extended
run, (2) RTH-open continuation long conditioned on the overnight holding the prior RTH close,
(3) range-edge acceptance break, either direction. `score` deliberately not run — zero closed trades,
so there is nothing to separate from the placebo, and the first run is due at bar 1,000.

**Stopped at:** cursor **402/11287**, flat, equity $50,000, peak $50,000, drawdown $0, permitted $240
(×1.00), 0 closed trades.

---

## Burst 3 — bars 402→506. basis `d5c4803` (2026-09-28, autonomous firing)

**Nothing to escalate.** No leak warning (`score` not due — 1 closed trade, first run at bar 1,000),
no absorbing state (drawdown $0, peak equity), no callout-id assertion (16 callouts, 16 unique ids),
series not ended. Briefs unchanged since burst 2.

### Result: 104 bars, 7 callouts, **1 trade taken and closed a winner**

**`R1-00014-b000453` — SHORT 3 MES @ 5791.75, stop 5804.0, target 5768.0 → TARGET, net +$348.18,
+1.895R. Equity $50,000 → $50,348.18.** One trade, one win. That is a sample of one and means nothing
statistically; it is recorded because it is the first time the process completed end to end.

Only 104 bars against the 400 asked for, because I switched to n=1 bar advances to manage a live
position and to stop walking past my own triggers. That trade-off is deliberate and I would make it
again — see below.

### The trade

Price broke the 5801–5927 range down to 5724.25, then rallied back to retest. **Bar 452 poked 5803.0
above the broken 5801 low and closed 5792.0 back below it on 203,196 — the heaviest bar of the leg.**
I shorted the failed retest at the next open, stop at the rejection bar's high plus a tick (12.25
points as filled), target 5768.0 inside the day's existing range so it did not need a new low to pay.
Bar 453 held under the stop (high 5801.0), bar 454 closed 5777.0, bar 455 filled the target.

**The first candidate in 455 bars whose stop was both structural and ≥ 0.5 ATR.** Every earlier one
failed that test: the overnight tape kept offering 4–5 point stops against a 6.9–17.1 ATR whose floor
was 3.5–8.6. Rule 4 was not an obstacle I worked around, it was the thing that disqualified nine
candidates and then passed this one.

**A defect in my own specification, declared before I acted on it.** My bar-441 sentence set the
short's invalidation at "a close back below 5751.5" — 40 points below the shelf, a nonsense trigger
for a shelf entry. I did **not** treat that sentence as satisfied. I acted on the *general* one-bar
method pre-stated at bar 431, applied to a level (5801) and a direction (short, with the trend) both
on record since bar 426. That distinction is the whole difference between executing a plan and
inventing one after the bar, and if a reviewer thinks I got it wrong, the `why` field carries the
reasoning to judge.

**The harness, not me:** it filled at 5791.75 against bar 453's open of 5792.0 (its tick of slippage),
sized **3** contracts at $183.75 rather than the 4 I estimated, and booked 1.895R against the 2.0 I
specified. Every one of those is a number I could have flattered myself with and none of them was mine
to write.

### Three more missed triggers, and the third one falsified my own fix — which is the useful part

| # | trigger | fired at | would have paid | why I missed it |
|---|---|---|---|---|
| 2 | close below 5837.5, next fails to reclaim | bar 414 | entry 5832.0, target 5801 hit bar 423 ≈ **2.3R** | advanced 25, it fired mid-chunk |
| 3 | close below 5801.0, next fails to reclaim | bar 429 | entry 5761.5, target 5775 **already passed** | advanced 5, still landed one bar late |
| 4 | close below 5730.0 (armed) | 11/04 low 5724.25 | untested | advanced 50 because the level was "33 points away" |

**Miss 3 is the one that taught me something, because it falsified the fix I had just invented.** At
bar 427 I replaced chunk-size-halving with distance-sizing and went to n=5 — and still missed by one
bar. The mechanism is arithmetic and I should have seen it immediately: **a two-bar trigger requires me
standing exactly on the second bar, so with any n > 1 I miss it with probability ≈ (n−1)/n.** Chunk
size never was the fix. Only n=1 while a trigger is armed actually works.

**And a substantive finding, not just an operational one: my acceptance filter had overcorrected.** I
added the second confirmation bar at bar 276 to kill the tick-through false break that had cost me at
bar 263. On a tape moving 27–32 points a bar, that filter confirms ~40 points past the level — bar 428
fell 32, bar 429 another 27, and my target was hit *before* the entry confirmed. **On 60m MES a two-bar
acceptance filter costs more in entry price than it saves in false breaks.** The version I settled on,
and then traded successfully, is one bar: enter on the close beyond the level, fill at the next open,
stop at that bar's opposite extreme. Neither the tick-through (too loose) nor two bars (too late).

Miss 4 broke a rule I had written 15 bars earlier: I advanced 50 with a trigger still armed, reasoning
that 33 points was "nothing pending". Thirty-three points is ~3 ATR and this tape covers it in two or
three bars. **Distance was the wrong variable. Tightened: while any trigger is armed, n ≤ 10, full
stop; n=50 only when nothing is armed.** I have now broken my own cadence rule in three consecutive
bursts, each time a different way, which says the rule needed to be about arming rather than distance.

### The tension this firing exposed, stated plainly for the account owner

**This exercise cannot both cross 11,287 bars and execute its own triggers faithfully.** Advancing
n=1 near a level is the only thing that works, and at that rate the series is unreachable. Advancing
50 is how three winners were walked past. I have chosen **fidelity over span** and this firing's 104
bars is what that costs. A record of a few honestly executed decisions is worth more than a tour of
eleven thousand bars I never really looked at, and the brief's own framing — "a record of how a
structured read behaves" — supports that choice. If the owner wants span instead, the honest way to
get it is a harness change (a standing-order / armed-trigger primitive the engine evaluates bar by bar
while I advance in large chunks), not me pretending 50-bar hops are a process. **That is a harness
request, not something I will build — `workspace/roundtable/` is not mine.**

### Bars passed over

Roughly **88 of the 104** advanced without a recorded candidate: overnight hours at 2–10k volume, the
16:00 forbidden bars, and one 50-bar hop whose middle (bars 456–487) I summarised from
`visible.jsonl` afterwards rather than examining bar by bar — recorded here because pretending I
looked at them would be the same species of dishonesty as backfilling an outcome.

### Distinct theses tried so far: **5**

Honestly and generously enumerated, because a wider count raises my own deflation threshold and that
is the direction to err in: (1) trend-continuation long on an extended run; (2) RTH-open continuation
long conditioned on the overnight holding the prior RTH close; (3) two-bar range-edge acceptance
break; (4) one-bar close-beyond-level break; (5) failed retest of a broken level — the one I traded.

`score` not run: 1 closed trade has nothing to separate from a placebo. First run due at bar 1,000.

### Carried into the next firing

Both short levels (5837.5, 5801, 5730) are **stale and disarmed** — the 5927→5724.25 downtrend
V-bottomed on 11/04 and 11/05 rallied to 5824.5, putting price back inside the old 5801–5927 range at
5816.0. I will not carry dead triggers. Nothing is armed, so the next firing opens at n=50 and arms a
fresh level once the reversal's structure is legible.

**Stopped at:** cursor **506/11287**, flat, equity **$50,348.18**, peak $50,348.18, drawdown $0,
permitted $240 (×1.00), **1 closed trade, 1 win, +1.895R**.

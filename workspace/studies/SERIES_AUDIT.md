# The roll and scale audit — every price series in this repository, measured absolutely

**Written by:** parent session, 2026-09-27. **Tool:** `workspace/roundtable/lib/scale_audit.py`
(parent-owned per `OWNERSHIP.md`). **Raw output:** `workspace/studies/out/series_audit.json`.
**Command:** `python3 workspace/roundtable/lib/scale_audit.py --json workspace/studies/out/series_audit.json`

**Coverage:** all 29 `data/archive/*.jsonl` and all 48 `csv/raw/*.csv` — 77 series, every symbol and
every timeframe this repository holds. Nothing under `csv/` was written to; it was read only.

## Why this exists and why it is first

`DEFECTS.md`'s first D-candidate records that `data/archive/MGC_1440m.jsonl` splices two instruments
and that *"checking a series' own extremes for a scale break is one line and nobody had run it."*
`yahoo.py` sets `auto_adjust=False` and has **no roll handling of any kind**, so every long series
buys `D40` at every expiry. EF5 named the missing roll audit as the one hazard it could not clear.

Per `BRIEF.md`'s independence clause — **measure absolutely before you measure relatively** — every
series is measured on its own terms. A relative test cannot find a hole two series share, which is
how a 51-hour vendor gap spanning COMEX *and* NYMEX was nearly missed.

Nothing here is a trading statistic. This is a **gate**: a series that fails is not eligible to
carry one.

## What the tool checks

| check | what it measures |
|---|---|
| **scale** | largest bar-to-bar close step; for every step above 3×, whether the segments either side have **disjoint** price ranges — a change of instrument, not a return. Plus `max(close)/min(close)`, the one-line extremes test. |
| **roll** | the bar-boundary gap `open[i+1] / close[i]`, bucketed, sign-tested, and split by month parity. COMEX gold's active months are the six **even** months; a roll-contaminated unadjusted front month shows same-signed excess there. |
| **shape** | rangeless bars (`h == l`), zero-volume bars, OHLC ordering violations. |
| **clock** | duplicate timestamps, non-monotonic timestamps, the largest calendar hole. |

---

# 1. The MGC daily splice — confirmed exactly, and it is the smaller of the two problems

BT6's finding reproduces to the digit, and the disjoint-range test names it a splice rather than a
jump:

```
index 383  2012-04-25  c =  164.10      pre-segment  [131.70,  188.90]   384 bars
index 384  2012-04-27  c = 1664.80      post-segment [1050.80, 5318.40] 3624 bars
ratio 10.145x        disjoint_ranges = True
max(close)/min(close) over the whole file = 40.38
```

**Only one step in 4,007 exceeds 100%, and it is this one.** So the file is one splice, not many:
drop the first 384 bars and the scale break is gone. The two segments also have **different defect
signatures**, which is independent evidence they are different instruments:

| segment | bars | span | rangeless | zero-volume |
|---|---|---|---|---|
| pre `[0:384]` | 384 | 2010-10-04 → 2012-04-25 | 77 (20.1%) | 1 (0.3%) |
| post `[384:]` | 3624 | 2012-04-27 → 2026-09-25 | 474 (13.1%) | 354 (9.8%) |

**No other series in this repository contains a splice.** The disjoint-range test fires on exactly
one file of 77. `MGC_1440m` was the only one, and it is now bounded.

**So the truncated series is 14.41 years, `sqrt = 3.796`.** That is the span the account was hoping
for — and §2 is why it is still not available.

# 2. The roll audit: MGC daily fails decisively, MES and MNQ daily pass

The decomposition that settles it. A series' total log return is exactly the sum of its **intraday**
moves (`close/open` within each bar) plus its **boundary gaps** (`open[i+1]/close[i]`):

| series | span | total | intraday | gaps | even-month gap | odd-month gap |
|---|---|---|---|---|---|---|
| **MGC_1440m post-splice** | 14.41 y | **+0.9461** | **−2.0079 (−212%)** | **+2.9584 (+313%)** | **+13.3 bp** | +3.1 bp |
| `csv/raw/MGC_1d` (frozen) | 9.98 y | +1.1777 | −0.5411 (−46%) | +1.7215 (+146%) | **+11.1 bp** | +2.6 bp |
| MES_1440m | 7.40 y | +0.9736 | +1.0490 (+108%) | −0.0753 (−8%) | +0.2 bp | −1.0 bp |
| MNQ_1440m | 7.40 y | +1.3680 | +1.2110 (+89%) | +0.1569 (+11%) | +1.2 bp | +0.5 bp |

**Read the MGC row.** Buying every daily open and selling every daily close over 14.4 years loses
**87%**, while the price rises 158%. The entire appreciation — and 3.1× more besides — lives in the
gaps *between* bars. That is the textbook signature of an unadjusted continuous front month: the
quoted level steps up at each roll into a higher-priced deferred contract, while the contract you
actually hold decays toward spot.

**And the gaps are where the roll is.** Large gaps (|gap| > 0.75%) in the post-splice segment:

```
498 large gaps: 304 up / 194 down      two-sided sign test  p < 0.0001
by month:  Feb 58  Apr 75  Jun 65  Aug 65  Oct 70  Dec 55     (even = 388)
           Jan 16  Mar 29  May 20  Jul 21  Sep 11  Nov 13     (odd  = 110)
```

**A 3.5× excess of large gaps in exactly the six active COMEX gold delivery months, upward-biased at
p < 0.0001.** The excess of the even-month mean gap over the odd-month mean, applied across the
even-month boundaries, is **+1.85 log units — 5.4× the price**, which is an upper bound on the
artefact rather than a point estimate, but it is the right order of magnitude and it dwarfs
everything the programme has ever measured.

**The same pattern is in the frozen substrate.** `csv/raw/MGC_1d` — 2,511 bars over 9.98 years, no
splice, `PROVISIONAL-SUBSTRATE` does not apply because it *is* `csv/raw` — shows +11.1 bp even-month
against +2.6 bp odd-month and an intraday sum of −0.541 against a gap sum of +1.722. **So this is
not an archive defect and it is not the splice. It is the vendor's roll convention, and it is in
both stores.**

**MES and MNQ daily pass.** Their gap sums are −8% and +11% of total return, their large gaps are
sign-neutral (19/31, p = 0.12; 46/42, p = 0.75), and they show no month-parity structure. Equity
index futures carry a roll spread small against daily volatility, so the roll does not dominate.
Their daily series are usable.

**CL daily is disqualified on a different ground** — see §4.

## Verdict on the span route

| substrate | clean span | √years | Sharpe to clear `free_t` 5.46 | `free_t` 3.505 (n≈465) | `free_t` 1.177 (one hypothesis) |
|---|---|---|---|---|---|
| published `scan_reports/` span | 0.88 y | 0.939 | **5.82** | 3.73 | 1.25 |
| **MES / MNQ daily** | **7.40 y** | **2.720** | **2.01** | **1.29** | **0.43** |
| MGC daily truncated — **FAILS the roll audit** | 14.41 y | 3.796 | (1.44) | (0.92) | (0.31) |
| `CL_1440m` — **FAILS, negative price** | 24.64 y | 4.964 | (1.10) | (0.71) | (0.24) |

**So the span route is open, and it is narrower than the 25.7-year version that was withdrawn.**
The honest statement:

> **7.40 years of roll-clean daily history exists, on MES and MNQ. It drops the required annualised
> Sharpe from 5.82 to 2.01 at programme-wide search width, to 1.29 at the width a genuine top-10
> selection needs, and to 0.43 for a single pre-registered hypothesis. The last of those is an
> ordinary number.**

**And the catch that must travel with it.** MES and MNQ are **one index complex** (`D14`/`D41`,
0.5–0.8% shared rule sets — agreement between them is not corroboration), so this is **one
independent observation, not two**. The two genuinely independent clean contracts are MGC and MCL:
MGC daily fails the roll audit, `MCL_1440m.jsonl` is **one bar**, and `CL_1440m` is disqualified.
**There is no roll-clean long daily series for either independent contract.**

# 3. The finding nobody was looking for: the bars are not contiguous, and the engine fills on it

`engine.py:290` and `:355` — **entries fill at the next bar's open** (`entry = spec.round_to_tick(bar.open + sign * slip)`),
which is the correct look-ahead discipline and is documented at `engine.py:8`. That makes
`open[i+1]` a price this repository has executed ~3M times.

**On this vendor's data `open[i+1]` is usually not `close[i]`, even where no time passes at all.**
Measured on contiguous boundaries only — consecutive bars exactly one bar-width apart, no session
break, no weekend, no halt:

| series | `open == prior close` exactly | contiguous boundaries | mean gap | median gap | sum |
|---|---|---|---|---|---|
| MGC 60m | 2,292 / 11,296 (20.3%) | 10,793 | **+0.50 bp** | +0.00 bp | **+0.5386** |
| MCL 60m | 3,279 / 10,933 (30.0%) | 10,380 | +0.25 bp | +0.00 bp | +0.2604 |
| MES 60m | 4,874 / 11,286 (43.2%) | 10,778 | −0.14 bp | +0.00 bp | −0.1505 |
| MGC 5m | 2,360 / 11,215 (21.0%) | 11,174 | +0.01 bp | +0.00 bp | +0.0142 |
| MGC 1440m post-splice | 48 / 3,623 (1.3%) | 3,133 | **+7.50 bp** | **+3.81 bp** | **+2.3484** |

**On MGC 60m, +0.5386 of the series' +0.4816 total log return — 112% of it — accrues at boundaries
where zero time elapses.** On MGC daily the *median* contiguous gap is **+3.81 bp**, meaning more
than half of all daily boundaries open above the previous close; that is a systematic bias, not
noise.

**What this does and does not mean.**

- It is **not** a look-ahead: the engine is filling on the correct bar.
- It is **not** a net cost: a gap up is a worse long fill and a better short fill, so the harm is a
  **direction-dependent asymmetry in measured expectancy**, of a size set by the data feed rather
  than by the market. On MGC that asymmetry is upward and persistent.
- It **is** a reason no `close[i]`-referenced price in this repository is a tradeable transition
  price. Anything that computes a stop, a target or a band from `close[i]` and then fills at
  `open[i+1]` is working across a discontinuity 57–80% of the time.
- Its size is **~1–1.5% of one R at 60m** on plausible stop geometry and materially more at 1440m.
  Small per trade, systematic across all of them, and never once accounted for.

**This is a D-candidate and the manager allocates the number (R-9).** It is the sixth mechanism in
the family whose signature is silent: it does not produce a null, it produces a *sign*, on a
programme whose central negative is about signs.

# 4. `CL_1440m` carries a negative price, and it is the only deep MCL-family daily series

```
close_min = -37.63   on 2020-04-20     (bars with close <= 0: 1;  bars with low <= 0: 2)
largest close step: 18.27 -> -37.63    = -305.97%
next boundary gap : -62.80%            2020-04-21
14 bars with 0 < close < 20
```

That is the real WTI settlement of April 2020, faithfully recorded. It is also arithmetically fatal
to everything this repository computes: `log(c/o)` is undefined, a percentage return is meaningless,
`atr_percentile` and every band are unbounded, and `max(close)/min(close)` does not exist. The audit
tool itself had to skip those steps.

**Why it matters more than one bad bar.** Board fact 5(b) records that `MCL_1440m.jsonl` is one
line, so MCL has no daily history. `CL_1440m` — 6,192 bars, 24.64 years — is the obvious substitute
and someone will reach for it. `BRIEF.md` already rules that full-size `CL=F` is not a substitute for
MCL on price grounds (0.95¢ mean close difference, 4¢ at worst). **This adds an arithmetic ground:
the series contains a region where the library's own arithmetic is undefined**, plus 881 large gaps
with no month structure (crude's roll spread flips sign with the curve, so a sign test cannot detect
it — 467 up / 414 down, p = 0.08) and single gaps of +31.07%, +26.34% and −20.37%.

**Second D-candidate. `CL_1440m` is not eligible to carry a statistic** unless the negative-price
region is excluded by name and the exclusion is reported.

# 5. Two more things the absolute sweep found, both already suspected and neither measured

**The grain contracts are mostly flat bars.** `D40` excluded them for splicing contract months. On
their own terms they are worse than that:

| series | rangeless (`h == l`) | zero-volume |
|---|---|---|
| `csv/raw/MZC_1m` | **567 / 639 (88.7%)** | 0.8% |
| `csv/raw/MZS_1m` | 556 / 637 (87.3%) | 0.8% |
| `csv/raw/MZW_1m` | 464 / 551 (84.2%) | 0.9% |
| `csv/raw/MZC_5m` | 1,615 / 2,567 (62.9%) | 0.8% |
| `csv/raw/MZC_1h` | 1,269 / 4,830 (26.3%) | **11.3%** |

A rangeless bar has zero range, so ATR, every band half-width, `range_position`, the opening range
and the noise-floor clamp all degenerate on it — **`D45`'s mechanism, on 26–89% of bars rather than
on the first bar of a session.** The exclusion stands and now has a second, independent reason.

**`QQQ` and `SPY` intraday carry no volume at all.** 58.2–59.4% of `QQQ_1h`, `QQQ_5m`, `SPY_1h` and
`SPY_5m` bars have `volume == 0`, against 0.0% on their daily files. Any volume condition read off
those series is reading a vendor artefact. They are context files, not substrate, but nothing in the
tree said so.

**And a benign one worth recording so nobody re-finds it as a defect.** The ~3.5–4.0% zero-volume
rate on every 60m micro-futures series (MGC 440/11,297, MCL 433/10,934, MES 420/11,287, MNQ
418/11,291, and ES/NQ/MES/MNQ in `csv/raw` at 3.5–3.7%) is uniform across four contracts and two
stores. It is the thin overnight hour, not a hole. 334 of MGC daily's 355 zero-volume bars are also
rangeless — they are synthetic no-trade bars, consistent throughout.

**No series has an OHLC ordering violation, a duplicate timestamp or a non-monotonic timestamp.**
77 of 77 clean on all four. The clock and the bar arithmetic are sound; it is the price scale, the
roll and the bar contiguity that are not.

---

# What this gates

| decision | ruling |
|---|---|
| `data/archive/MGC_1440m.jsonl` bars 0–383 | **not eligible for any statistic.** Different instrument. |
| any MGC daily row, either store, unadjusted | **not eligible.** Fails the roll audit at p < 0.0001 with the gap sum at 3.1× the total return. A roll-adjusted MGC daily series would be eligible; building one is new work. |
| `CL_1440m` | **not eligible** without a named, reported exclusion of the negative-price region. |
| MES / MNQ daily, 7.40 years | **eligible.** Roll-clean, splice-free, gap-immaterial. One index complex, so one independent observation. |
| MGC / MCL / MES / MNQ at 5m–240m | **eligible**, unchanged — no splice, no roll signature, the gap sums are small at 5m (2–15% of total). The 60m gap-dominance in §3 is a fill-asymmetry hazard, not an eligibility failure. |
| the grain contracts | **not eligible**, second reason. |
| `QQQ` / `SPY` intraday volume | **not eligible** as a volume input. |
| the 25.7-year span claim | **withdrawn and replaced by 7.40 years on one complex.** The required Sharpe is 2.01 at programme width and 0.43 for one pre-registered hypothesis, not 1.08. |

**Two D-candidates for the manager, described not numbered (R-9):** the non-contiguous bar boundary
the engine fills on (§3), and `CL_1440m`'s negative price (§4).

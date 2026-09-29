# AVENUES — DISC2's half of the discovery ledger

**Owner:** DISC2 (`OWNERSHIP.md`). **Neither half is the whole ledger.** DISC1 owns
`discovery/AVENUES.md` (69 avenues, burst 01). **Both are read in full before either is written**
(`OWNERSHIP.md`, "Two discovery agents, one memory"). Exploration is claimed first, in
`discovery/claims/<DISC>-<avenue-id>.md`, and a claim that already exists means pick another.

| verdict | meaning | may a later burst revisit? |
|---|---|---|
| `CLOSED-EMPTY` | explored, nothing there | **no** — not without a new reason, stated |
| `CLOSED-FOUND` | explored, produced a main task | no — the main task carries it now |
| `OPEN-PARTIAL` | explored to a stated depth, more remains | yes, **from the recorded stopping point** |
| `DEFERRED` | out of reach for a named reason | only if that reason changes |

## Conventions this file adopts, and why

1. **Avenue ids are DISC1's.** `II-7`, `X-12` and the rest are allocated in
   `discovery/AVENUES.md`; I reuse them rather than minting a parallel numbering, because two
   numberings for one map is the failure the registry was written to stop
   (`REGISTRY.md`, "The collision that already happened").
2. **I cannot change a verdict in DISC1's file and I do not try.** Where my sweep contradicts a
   DISC1 row, this file records **DISC2's verdict, DISC1's verdict, and the fact that they
   disagree**, and a message goes to DISC1 so the owner applies or refuses it. A silent cross-edit
   is how two agents come to hold different beliefs about what a file says.
3. **Rows marked `— POINTER, NOT VERDICTED BY ME —`** are measurements I made in passing that bear
   on an avenue I did **not** claim. They are handed to the owner. Treating them as verdicts would
   be claim-jumping by the back door.
4. **Numbered observations of my own use `DISC2-D<n>`**, which `check_refs.py`'s `ID` regex admits
   `[measured: sed -n '/^ID = re.compile/,/^)/p' workspace/roundtable/check_refs.py → "(R[1-6]|BT[1-6]|DISC2?)-(Q\d+|REQ-\d+|ALGO-\d+|D\d+[a-z]?|[AB]-\d+)"]`. It does **not** admit
   `DISC2-LEAD-<n>`, so I use no LEAD ids in a message header.

## Sources read in full before writing

`PIPELINE.md`, `OWNERSHIP.md`, `REGISTRY.md`, `BRIEF.md`, `discovery/AVENUES.md` (all 394 lines),
`discovery/MAIN_TASKS.md`, `msgs/05_manager_all_round2-board.md`,
`msgs/07_manager_discovery_lead05-and-x15.md`, `msgs/13_manager_all_D48-D49-and-triage.md`.
Targeted reads of `research/R2_relational.md`, `R2_expressibility_wall.md`, `R2_wall_a_spec.md`,
`R2_recut_contingency.md` at every `II-7` / `II-5` / `II-16` / cross-sectional hit.
`discovery2/AVENUES.md` did not exist `[measured: wc -l discovery2/AVENUES.md → No such file]`.
`discovery/claims/` was empty `[measured: ls -la → . and .. only]`.

---

## Burst 01 — the avenue I claimed

| id | avenue | DISC2 verdict | DISC1 verdict (`discovery/AVENUES.md`) | agree? |
|---|---|---|---|---|
| `II-7` | Cross-sectional momentum and cross-sectional carry across a futures universe | **`CLOSED-FOUND`** — carried by `MAIN-02` | `DEFERRED`, blocker "the universe is too small and too ragged", change-condition **"≥10 independent contracts with a common span"** | **No.** The change-condition is met. Measured below. |

### `DISC2-D1` — `II-7`'s blocker has lifted, and by a wide margin

The row's own change-condition is a *quantity of data*. It is now available from the vendor this
repo has already proven it can reach, with **zero code change** — `ticker_for` passes any root
through as `<ROOT>=F` and explicitly passes `^`/`=` symbols untouched
`[repo-verified: futures_agents/data/yahoo.py:100-116]`, and the daily lookback cap is
**25 years** `[repo-verified: futures_agents/data/yahoo.py:86 → 1440: ("1d", timedelta(days=365*25))]`.

`[measured: yfinance 1.7.0 batch download, interval="1d", 37 tickers, window 2016-09-26 → 2026-09-23,
availability probe only, nothing written →]`

**36 of 37 tickers returned 2,317–2,513 daily closes on a common span 2016-09-26 → 2026-09-22**,
spanning **10 sectors**: US equity index (ES, NQ, YM, RTY), rates (ZN, ZB, ZF, ZT), FX (6E, 6J, 6B,
6A, 6C), precious metals (GC, SI, PL), industrial metals (HG), energy (CL, NG, RB, HO, BZ), grains
(ZC, ZS, ZW, ZL, ZM), softs (KC, SB, CT, CC, OJ), livestock (LE, HE, GF), and `^VIX`.

`[measured: second probe, 11 tickers, window 2001-01-01 → 2026-09-23 →]` the span is not the
limit either: **ES=F 6,494 / ZN=F 6,459 / 6E=F 6,496 / GC=F 6,456 / CL=F 6,459 / ZC=F 6,453 /
KC=F 6,449 / HG=F 6,460 / NG=F 6,461 / ^VIX 6,470 daily bars, all beginning 2001-01-02**;
LE=F 6,406 from 2001-03-01. **A common 25.7-year daily span across ten sectors.**

**For scale against what this programme has actually searched:** every published `scan_reports/`
result rests on a 60-minute file of ~5,000 bars ≈ **274 trading days**
`[repo-verified: BRIEF.md; discovery/AVENUES.md burst-01 addendum]`. 25.7 years is **≈29× that
calendar span**, and none of it has ever been searched.

**So the honest statement of the blocker is that it was never a data blocker at all — it was an
unasked purchase order.** DISC1's row says as much in its own preamble for the class ("'we have no
series for X' is now a *purchase order*") and then does not apply it to `II-7`, because `II-7`'s
blocker is phrased as universe *size* rather than as a missing series.

### `DISC2-D2` — R2's `II-7` verdict is right about the disk and untested about the vendor

R2 states `II-7` more emphatically than any other Class II row, three times:
**"NO, and no amount of Wall A fixes it"** `[repo-verified: research/R2_wall_a_spec.md:89]`;
*"one (II-7) remains inexpressible regardless"* `[:103-104]`; and filed under
**"genuinely unobservable from here … a 40-market universe"**
`[repo-verified: research/R2_relational.md:918, 1267]`. The stated reason is universe size:
*"the canonical version ranks 40-60 markets; here N=4 … the effective cross-section is closer to
**2**"* `[repo-verified: research/R2_expressibility_wall.md:186]`.

**Every one of those claims is about the universe on disk, and on disk R2 is correct.** I checked:
`[measured: ls csv/raw/*_1d.csv → MES, MGC, MNQ, QQQ, SPY only; MES 1,859 (2019-05-03→2026-09-21),
MGC 2,511 (2016-09-26→…), MNQ 1,859, QQQ 2,512, SPY 2,512]`. Four of those five are the US equity
index; one is gold. Daily in the archive adds `CL_1440m` and a one-row `MCL_1440m`
`[measured: below]`. **Effective cross-section on disk: 2, possibly 3.**

What I could not find anywhere is a test of the *acquisition* claim. "A 40-market universe" is
filed as a real acquisition alongside "an options surface" and "a news feed" — objects that are
genuinely hard — when it is in fact one batch call to a vendor already in use. **I am not
contradicting R2's expressibility verdict; I am contradicting the premise under its data verdict,
and only the premise.** Wall B is still required to *trade* a cross-section. Nothing here needs
Wall B to *measure* whether one exists.

### `DISC2-D3` — the cheap half is bars; the expensive half is contract specifications

The cost of the universe is not the data. It is **28 `ContractSpec` entries.**

`[measured: python3 -c "from futures_agents.config import CONTRACTS; ..." → CONTRACTS holds 21
roots: CL, ES, GC, M2K, M6E, MCL, MES, MGC, MNG, MNQ, MYM, MZC, MZS, MZW, NQ, QQQ, RTY, SIL, SPY,
YM, ZN. Of the 35-future basket, **7 have a spec** (ES, NQ, YM, RTY, ZN, GC, CL) and **28 do
not**]`. Each missing spec is `tick_size`, `point_value`, `commission_per_side`,
`exchange_fee_per_side`, `typical_slippage_ticks`, `min_stop_ticks`, `typical_atr_points` — real
world facts to be looked up, not derived, and **exactly the fields that decide whether a market is
tradeable at all.** `config.py:100-101` promises the rest is automatic: *"Add a contract here and
the whole system — backtests, sizing, journaling, per-symbol strategy groups — picks it up
automatically."* `[repo-verified: futures_agents/config.py:100-101]`

Two things already exist that a cross-sectional study needs and that nobody has connected to one:
`correlation_group` already carries a **sector taxonomy** — `ENERGY`, `FX_MAJORS`, `GRAINS`,
`PRECIOUS_METALS`, `RATES`, `US_EQUITY_BROAD`, `US_EQUITY_SMALL`, `US_EQUITY_TECH`
`[measured: sorted set over CONTRACTS → 8 labels]` — and the registry **already holds `ZN` (10-year
note) and `M6E` (micro euro) specs for which no price series exists in either store.** The contract
registry anticipated rates and FX; the data never arrived.

### `DISC2-D4` — the repo's only mention of a cross-section is a disclaimer

`[measured: grep -ril over the whole repo excluding roundtable/, .git, __pycache__ → "cross
sectional/cross-sectional" 5 files; "time series momentum" 0; "managed futures" 0; "\bCTA\b" 0;
"Moskowitz" 0; "trend follow" 0; "Donchian" 0; "risk parity" 0; "volatility target" 0]`.

All five "cross-sectional" hits are either a **survivorship-bias disclaimer** — *"single continuous
front-month series per symbol; **no cross-sectional selection is performed**"*
`[repo-verified: workspace/strategy_research/w3_publish.py:249;
workspace/strategy_research/rank_nq_es_grains_robustness_report.json:10]` — or a remark that two
symbols behaved differently `[repo-verified: workspace/studies/merged.json:1544]`. The 18
`long.short` hits are all trade *direction*, not a long-short portfolio
`[measured: grep -ril, paths inspected]`.

**So the absence of a cross-section is recorded in this repo as a virtue** (it is listed among the
mitigations in a robustness report) rather than as an untested family. That is a reasonable thing
to have written and it is probably part of why nobody built one.

### `DISC2-D5` — the arithmetic that reframes the programme's own gate, and the sharpest item in this sweep

Stated as arithmetic with its assumption named, **not** as a re-litigation of the settled null.

For a return series, `t ≈ SR_annualised × sqrt(years)` `[general knowledge — Lo (2002), "The
Statistics of Sharpe Ratios"]`. The repo's gate is `free_t = sqrt(2·ln n)` with `n` the number of
variants searched `[repo-verified: workspace/studies/toolkit.py:58 →
math.sqrt(2.0 * math.log(max(2, trials)))]`.

| sample length | sqrt(years) | annualised Sharpe needed for `t = 5.46` | … for `t = 3.923` (largest ever found here) |
|---|---|---|---|
| **274 sessions / 322 calendar days ≈ 0.88 yr** (every `scan_reports/` hourly result) | 0.94 | **≈ 5.8** | ≈ 4.2 |
| 9.75 years (MGC daily, the chronology study) | 3.12 | ≈ 1.75 | ≈ 1.26 |
| **25.7 years** (the vendor's common daily span, measured above) | 5.07 | **≈ 1.08** | ≈ 0.77 |

**Two consequences, and I am claiming only the first.**

1. **`free_t` and sample length are two knobs and this programme has only ever turned one.** On a
   274-day sample the gate demands a Sharpe of roughly 5.8, which no documented strategy in any
   asset class has ever sustained `[general knowledge]`. So "nothing clears its own threshold" is,
   on that sample, **partly an arithmetic property of the sample length** rather than only a
   statement about the strategies. This does **not** rescue any strategy and does not contradict
   BRIEF's settled verdict — it says what *else* determines the verdict, and the direction is
   inconvenient rather than convenient: it implies the largest `t` ever found here (3.923, needing
   Sharpe ≈ 4.2 on that span) is *more* likely to be an artefact, not less.
2. **The repo's own deflation floor for a single pre-registered hypothesis is `1.177`, not `5.46`.**
   `max(2, trials)` means `trials = 1` returns `sqrt(2·ln 2) = 1.1774`
   `[repo-verified: workspace/studies/toolkit.py:58]`. A family taken from the literature and
   tested once here is not mined *here*. **The counter, which is heavy and belongs beside it:** the
   literature's surviving families are themselves the output of a large, undocumented, decades-long
   collective search, so the honest `n` is not 1 — it is unknown and large. That is precisely why a
   never-searched sample matters more than a threshold argument, and it is why `MAIN-02` is framed
   as a diagnostic rather than as a candidate.

---

## Pointers, not verdicts — measurements bearing on rows I did **not** claim

Handed to the owner. **I did not claim these avenues and I am not re-verdicting them.**

| row | owner | what I measured in passing |
|---|---|---|
| `II-5` inter-market | DISC1's row; R2's family | **The ticker DISC1's change-condition names is dead.** DISC1 writes *"Change-condition: one fetch via `yahoo.py` (`^TNX`, `DX=F`, `6E=F`)"*. `[measured: probe → `DX=F` returns HTTP 404, "Quote not found for symbol: DX=F", 0 bars — the only failure of 37]`. `6E=F` returns 2,511 bars and `ZN=F`/`ZB=F`/`ZF=F`/`ZT=F` all return ~2,511, so **the rates and FX legs are available and the dollar-index leg as specified is not.** A dollar basket from 6E/6J/6B/6A/6C, or the spot index under a different ticker, would substitute; I did not test either. |
| `II-16` volatility as a traded object | DISC1's row; R2's family | `^VIX` returns **2,513 daily bars on the 2016→2026 span and 6,470 from 2001-01-02** `[measured: both probes]`. R2 filed II-16's IV-vs-RV arm as *"absent but vendor-reachable with zero code change"* `[repo-verified: R2_relational.md:917]` — that is now **measured** rather than expected. The **VX term-structure arm is untouched by this**: it needs per-expiry tickers, which I did not probe. |
| `II-4` inter-commodity spreads | DISC1's row | DISC1's blocker is *"only one leg of each pair is present"*. `[measured: RB=F 2,512, HO=F 2,512, BZ=F 2,512, ZM=F 2,510, ZL=F 2,510, SI=F 2,510 — all present]`. So crack (CL/RB/HO), crush (ZS/ZM/ZL) and gold-silver legs are all vendor-reachable. **The wheat-corn note stands unchanged and is the warning, not the opportunity** — see `X-12`/D40 row below. |
| `X-12` the new data stores | DISC1's row | DISC1 states the archive's **hourly** consequence (~11,300 bars/symbol, +~6,000 before the published span). **The daily consequence is different and larger and is not stated anywhere:** `[measured: python3 over data/archive/*_1440m.jsonl → CL 6,192 bars 2002-02-05→2026-09-25; MGC 4,008 bars 2010-10-04→2026-09-25; MES 1,863 2019-05-03→…; MNQ 1,863; MCL **1 row**]`. Against `csv/raw`: MGC daily gains **1,497 bars ≈ 6 years before the published daily span**, and **`CL_1440m` is a 24.6-year series with no `csv/raw` equivalent — the longest series in this repository, used by nothing.** |
| `III-1` CTA trend following | DISC1's row | DISC1's *"named only"* for the classic version is confirmed from a second direction: `[measured: "Donchian" 0 files, "time series momentum" 0, "managed futures" 0, "\bCTA\b" 0, "trend follow" 0]`. Time-series momentum is the same literature as `II-7` and the same three structural exclusions apply to both (see `MAIN-02`). |
| `X-15` deflation accounting | DISC1's row; manager closed the open half in ADJ-4 | `DISC2-D5` above is **not** the open half ADJ-4 closed (the denominator). It is a different quantity — the **numerator's sample length** — and no row in either ledger holds it. If it belongs anywhere it is a new row, and that is DISC1's or the manager's call, not mine. |
| `D40` grain splicing | programme defect | Read in full before writing `MAIN-02`. **It is not a `=F` artefact in general** — *"NQ and ES have zero flat bars and zero 2% gaps, so this is specific to the grains"* `[repo-verified: workspace/studies/DEFECTS.md, D40]`. But **5 of the 35 markets I probed are grains and 8 more are softs and livestock**, and D40's measured economics on the thin end are brutal: round-turn fees **9.2% of one R on MZC vs 0.17% on NQ**, 26.3% flat bars, 11.3% zero-volume bars. A broad universe is broad *because* it includes the thin markets. **This is the counterweight `MAIN-02` must carry, and it is the cheapest way to kill it.** |

---

## What I deliberately did not do in this burst

- **No backtest, no sweep, no ranking, no expectancy, no z-score.** Nothing above is a performance
  statement about any strategy.
- **No write to `data/archive/`** (append-only, not mine) and **no write of any kind under `csv/`**.
  The probes downloaded into memory, printed counts and date bounds, and kept nothing.
- **No test of the roll convention**, which is `MAIN-02`'s first gate. `yahoo.py` applies
  `auto_adjust=False` `[repo-verified: futures_agents/data/yahoo.py:305]` and contains **no roll
  handling of any kind** `[measured: grep -in "roll|continuous|front.month|adjust"
  futures_agents/data/yahoo.py → 3 hits, one of them the `MNQ=F` ≠ `MNQ1!` warning at :13, one an
  `auto_adjust=False` kwarg, one an unrelated comment]`.
- **No per-expiry probe.** Whether the vendor serves individual contract months — which would move
  `II-1`, `II-2`, `II-18`, `III-15` and `II-16`'s term-structure arm — is untested. It is the single
  cheapest unasked question left after this burst and it is **not mine**: those are DISC1's rows and
  R2's families. Logged here so it is not lost.
- **No statistical measurement on the probed series.** I did not compute a return, a correlation, a
  rank or a premium. `DISC2-D5` is arithmetic on published figures, not a measurement of data.
- **No second sweep.** One burst, one question (`PIPELINE.md` §1).

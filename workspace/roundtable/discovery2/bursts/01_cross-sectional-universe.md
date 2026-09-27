# DISC2 burst 01 — did `II-7`'s blocker actually lift?

**2026-09-27.** One sweep, one question, one stopping point (`PIPELINE.md` §1).

## Before the sweep

Read in full: `PIPELINE.md`, `OWNERSHIP.md` (including the claim protocol at the end),
`REGISTRY.md`, `BRIEF.md`, **`discovery/AVENUES.md` — all 394 lines, 69 avenues**,
`discovery/MAIN_TASKS.md`, and three manager broadcasts (`msgs/05`, `msgs/07`, `msgs/13`) because
`BRIEF.md` requires answering the current state of the conversation rather than the state at launch.

**Claim protocol executed before anything else.**
`[measured: ls -la workspace/roundtable/discovery/claims/ → empty, . and .. only]` and
`[measured: wc -l discovery2/AVENUES.md → No such file or directory]`. No claim existed for any
avenue, so nothing was taken. `discovery/claims/DISC2-II-7.md` was written **before** the first
probe.

**Three avenues I ruled out before claiming, so the reasoning is on the record.**

| candidate | why not |
|---|---|
| `X-8` / `DISC-LEAD-05` — the name-vs-arithmetic audit of the remaining 11 condition groups | DISC1 named it *"the strongest candidate for burst 02's sweep"* in its own ledger, **and the manager has already split it three ways onto the board** as `MGR-T5`/`MGR-T4`/`MGR-T7` and invited DISC1 to promote it `[repo-verified: msgs/07_manager_discovery_lead05-and-x15.md]`. Taking it is the exact collision the claim protocol exists to prevent, whatever a claim file says. |
| `X-4`, `X-9`, `X-10`, `X-12`, `X-14` | DISC1 recorded an explicit resumption point or a numbered lead for each. `X-12` in particular is DISC1's *"deliberately not pursued in burst 01"* with `DISC-LEAD-04` attached. |
| `I-8` auction market theory — the most attractive untouched "named only" row | Genuinely unexplored and I nearly took it. Declined because its blocker is **architectural** (no object in the library represents excess, a single print or a value shift) and nothing about it changed this week, so it is not the cheapest discovery available; and because it abuts `I-7`, which is in flight with R1. **Recorded as the strongest remaining "named only" row for whoever sweeps next.** |

## The question

> `II-7` (cross-sectional momentum and cross-sectional carry across a futures universe) is
> `DEFERRED` with the change-condition **"≥10 independent contracts with a common span."** The data
> policy moved this week. **Has that condition been met?**

Chosen because it is the only shape of avenue my brief singles out as the cheapest real discovery —
a `DEFERRED` row whose blocker is a *data* condition — and because its blocker is the one a second
reader can falsify in a single call rather than argue about.

## What the sweep did, in order

1. **Repo footprint.** `[measured: grep -ril over the whole repo excluding roundtable/, .git,
   __pycache__ → "cross sectional/cross-sectional" 5 files, all of them either a survivorship
   disclaimer or a remark that two symbols differed; "time series momentum" 0; "managed futures" 0;
   "\bCTA\b" 0; "Moskowitz" 0; "trend follow" 0; "Donchian" 0; "risk parity" 0; "volatility
   target" 0]`. No cross-sectional machinery exists; the only mentions are disclaimers.
2. **What is on disk.** `[measured: ls csv/raw/*_1d.csv → 5 files: MES, MGC, MNQ, QQQ, SPY; four of
   the five are the US equity index]`. `[measured: python3 over data/archive/*_1440m.jsonl → CL
   6,192 bars 2002-02-05→2026-09-25; MGC 4,008 from 2010-10-04; MES/MNQ 1,863 from 2019-05-03;
   MCL 1 row]`. **R2's "effective cross-section ≈ 2" is correct about the disk.**
3. **R2's verdict, read at every hit** rather than summarised from DISC1's reconciliation table.
   `II-7` is R2's most emphatic Class II row: *"NO, and no amount of Wall A fixes it"*, *"remains
   inexpressible regardless"*, filed under *"genuinely unobservable from here … a 40-market
   universe."* The stated reason is universe size, on disk.
4. **Vendor surface.** `[repo-verified: futures_agents/data/yahoo.py:100-116]` `ticker_for` passes
   any unknown root through as `<ROOT>=F` and passes `^`/`=` symbols untouched; `INTERVALS[1440]`
   caps daily lookback at **25 years** `[:86]`. **Zero code change needed for an arbitrary
   universe.**
5. **The probe** — availability only, prints counts and date bounds, keeps nothing, writes nothing.
   37 tickers across ten sectors, `interval="1d"`.

## The answer

**The blocker has lifted, and not marginally.**

- **36 of 37 tickers**, 2,317–2,513 daily closes, **common span 2016-09-26 → 2026-09-22**, ten
  sectors (US equity index, rates, FX, precious metals, industrial metals, energy, grains, softs,
  livestock, `^VIX`).
- On a 2001 start: **≈6,460 daily bars per market, common span 2001-01-02 → 2026-09-22 — 25.7
  years**, tested on 11 tickers drawn one per sector. That is **≈29× the calendar span of the
  274-session window every published `scan_reports/` result rests on**, and none of it has ever been
  searched.
- The single failure is **`DX=F` → HTTP 404, "Quote not found"** — which matters because it is one
  of the three tickers DISC1's `II-5` change-condition names by hand.

Full numbers, five numbered observations and the pointer rows are in `discovery2/AVENUES.md`.
`II-7` is `CLOSED-FOUND` in my half, carried by **`MAIN-02`**; DISC1's row still reads `DEFERRED`
and **only DISC1 can change that** — messaged, not edited.

## Where I stopped, and why there

**I stopped at availability. I did not compute one return, rank, correlation or premium from any
probed series.**

Why there and not one step further: the next step is not a cheap one, and taking it would have
produced a number nobody could interpret. **A Yahoo `=F` daily series has no documented roll
convention and `yahoo.py` applies no roll handling at all** — `auto_adjust=False` at `:305`, and the
module's own header warns `MNQ=F` is not `MNQ1!` precisely because of *"different roll convention"*
at `:10-13`. An unadjusted front-month series gaps at every roll and a momentum signal reads that
gap as a return. **This repo already has that failure numbered — D40**, where a spliced continuous
series produced 367 close-to-open gaps above 2% on MZC, 47% of which fully reverse. So any momentum
statistic I computed today would have been a statistic about an unaudited splice, which is this
repo's single most frequent documented failure mode: a real-looking result from a broken detector.
**Naming the gate and stopping is the correct outcome; it is also the cheapest way to kill
`MAIN-02`, which is a good property for a main task to have.**

The second reason to stop: one burst, one sweep. A gap diagnostic across 36 markets is depth, and
depth is somebody else's job (`PIPELINE.md` §1).

## What this burst deliberately did not do

- No backtest, no sweep, no expectancy, no z-score, no ranking. Nothing here is a performance claim.
- No write to `data/archive/` (append-only, not mine); **no write of any kind under `csv/`**, ever.
- No edit to any file owned by another agent. Two corrections that belong in DISC1's ledger
  (`II-5`'s dead `DX=F`, and `X-12`'s unstated *daily* consequence) went out as a message.
- No per-expiry probe — untested, and it is the cheapest unasked question left after this burst. It
  would move `II-1`, `II-2`, `II-18`, `III-15` and `II-16`'s term-structure arm, and it decides
  whether the **carry** half of `II-7`'s own title is reachable. Not mine: those are DISC1's rows.
- No second claim, no negotiation over an existing one, and no sweep of an avenue someone else had
  declared intent on.

## One thing I found that is bigger than the avenue, recorded as `DISC2-D5`

`t ≈ SR × sqrt(years)` `[general knowledge — Lo (2002)]`. On the 274-session / 322-calendar-day span
that carries every published result here, `sqrt(years) = 0.94`, so clearing `free_t = 5.46` requires
a sustained annualised Sharpe of **≈ 5.8** — beyond anything documented in any asset class. **The
programme has two knobs, search size and sample length, and has only ever turned one.** This does
not rescue any strategy and does not contradict `BRIEF.md`'s settled verdict; the direction is
unfavourable, since it makes the largest `t` ever found here (3.923, needing Sharpe ≈ 4.2 on that
span) look *more* like an artefact. It also means the repo's own gate for a single pre-registered
hypothesis is **1.177**, not 5.46 — `max(2, trials)` at `workspace/studies/toolkit.py:58` — with the
heavy counter that the literature's survivors are the output of a large undocumented search, so the
honest `n` is not 1. Full statement, both readings and the counter-argument in
`discovery2/AVENUES.md` `DISC2-D5`; raised with the manager because it is not `X-15`'s closed
denominator question and no row in either ledger holds it.

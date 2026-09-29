# EF3 burst 01 — substrate for MES/MNQ at 60m and 240m

**Cell:** SWING, MES + MNQ, 60m + 240m. **Store:** `data/archive/` (per BRIEF's BT1-REQ-1 ruling).
**Code:** `workspace/roundtable/edge/EF3/code/ef3_substrate.py`.

## Decision: one base series, 60m, with `timeframes=[60, 240]`

Both of my timeframes run on the **same 60-minute base series**, with the 240m frame produced by
`SymbolFrame`'s own `resample`. Reasons, in order of weight:

1. **The resample is bit-identical to the vendor's own 240m series**, so nothing is lost by it.
   `[measured: ef3_substrate.py → MES/MNQ: archive 240m 3,050 bars; resample(archive 60m→240m)
   3,050 bars; stamp sets identical True; 3,050/3,050 closes bit-exact; max|Δclose| 0.000e+00;
   0 volume mismatches]`
2. The engine manages positions on **base** bars (`engine.py:283` iterates `frame.base.bars`), so a
   60m base gives the 18:00→16:00 clock and every stop/target 4× the resolution a 240m base would.
   A 240m base cannot express "flat at 16:00" at all: its buckets are 4 hours wide and one of them
   straddles 16:00 (below).
3. It makes the 60m and 240m cells differ only by `primary_tf`, not by substrate.

## Store agreement (tolerance, never `==`, per BRIEF)

| symbol | archive 60m | csv/raw 1h | overlap | closes bit-exact | max abs Δclose | volume mismatches |
|---|---|---|---|---|---|---|
| MES | 11,287 | 5,000 | 4,988 | **4,988 / 4,988** | 0.000e+00 | 2 |
| MNQ | 11,291 | 5,000 | 4,988 | **4,988 / 4,988** | 0.000e+00 | 2 |

Matches BRIEF's corrected table for the index complex. Timestamps normalised to UTC on both sides
before comparison (the BRIEF's timezone trap).

## Span

718.9 calendar days = **1.968 years, sqrt = 1.403**. `t ≈ SR·sqrt(years)` ⇒ a sustained annualised
Sharpe of **0.839** is needed to reach `free_t = 1.177` (one pre-registered hypothesis) and
**3.892** to reach 5.46. Every threshold in my cell is quoted against 1.403, not against 1.0.

## Three grid facts the session rule turns on, and they are mine to carry

**(1) 240m bars are anchored to ET midnight, so one bucket in six straddles 16:00 ET.**
`align_bucket` puts multi-hour buckets on 00/04/08/12/16/20 ET `[repo-verified:
futures_agents/data/bars.py:150-154]`. The bucket labelled **16:00 spans 16:00→20:00**, i.e. it
contains the 16:00–17:00 hour (inside the prohibited window), the 17:00–18:00 CME break, and
18:00–20:00 of the *next* trading day. `[measured: 585 of 3,050 = 19.2% of 240m bars, both symbols]`
There is **no 4-hour bucket boundary at either 16:00 or 18:00 that separates the two sides** — the
boundary at 16:00 exists but the bucket that starts there crosses into the new session.
**Consequence: a 240m "bar close" is not a legal decision point under the 18:00→16:00 rule** and a
240m cell must take its decisions on the 60m grid. My design already does (see the base-series
decision above); a 240m-base design silently cannot.

**(2) 493 (MES) / 497 (MNQ) 60m bars are stamped 16:00–17:59 ET** — inside the flat window. Of those
only 5 (MES) / 9 (MNQ) are stamped 17:00–17:59, so the CME break is genuinely empty and the
prohibited window is essentially the single 16:00–17:00 bar per session.

**(3) The archive has 20 bars off the `:00` grid, and they are exactly five early-close
half-sessions** — 2024-11-29, 2024-12-24, 2025-07-03, 2025-11-28, 2025-12-24, four `:30` bars each,
at 09:30/10:30/11:30/12:30 ET, identical on MES and MNQ. This **differs from `csv/raw`**, where R3
measured the 1h grid as 100% `:00` (`msgs/11_R3_R1_re-stopkind-RANGE.md`). It matters because a
09:30 `:30` bar has `minutes_since_open = 0` against MES/MNQ's 09:30 RTH open, so the 30-minute
opening-range window **is** reachable on my substrate — on 5 sessions of ~490. See burst 02: this
turns two strict-VOID verdicts into NEAR-VOID ones and it is a property of the store, not of the
market.

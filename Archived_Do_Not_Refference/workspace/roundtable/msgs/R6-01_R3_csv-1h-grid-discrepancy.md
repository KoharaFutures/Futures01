RE:    D49
ALSO:  D-L1, R6-M3, research/R3_path_operation.md, research/R1_group_audit.md
FROM:  R6
TO:    R3
TASK:  round-1

# The open `csv/raw` 1h grid discrepancy resolves in R1's favour — R3's count is wrong

`research/R3_path_operation.md:2202-2213` reports one discrepancy "rather than adjudicating" it:

> R1's table gives MES 1h and MNQ 1h as 2/5000 bars in-window, attributed to two holiday
> half-sessions, which requires `:30` hourly bars to exist. My count of `csv/raw` finds the 1h grid
> **100% at `:00`** for the three files I checked … So on `csv/raw` the figure should be **0/5000,
> not 2/5000**, which makes R1's finding *stronger* than stated.

I was auditing `scan_reports/2026-09-24_ORB-and-ICT.md`'s claim that `snap.opening_range` is None on
4,990 of 5,000 MES 60m bars, which sits directly on this disagreement, so I measured it.

**R1 is right. The 1h grid is not 100% at `:00` — every one of the four files carries 8 off-grid
`:30` bars.**

`[measured: PYTHONPATH=. python3 -c "from futures_agents.data.loader import load_csv; from
futures_agents.timeutil import to_et, minutes_since_open; from futures_agents.config import
get_contract; import collections" — for each of csv/raw/{MGC,MES,MNQ,MCL}_1h.csv:
Counter(to_et(b.ts).minute) and the count of bars with 0 <= minutes_since_open(b.ts,
get_contract(s).rth_open) < 30]`

| symbol | minute histogram | `rth_open` | bars with `0 <= mso < 30` |
|---|---|---|---|
| MGC | `{0: 4992, 30: 8}` | 08:20 | **0** |
| MES | `{0: 4992, 30: 8}` | 09:30 | **2** |
| MNQ | `{0: 4992, 30: 8}` | 09:30 | **2** |
| MCL | `{0: 4992, 30: 8}` | 09:00 | **215** |

The eight `:30` bars are the same eight timestamps in all four files:

```
2025-11-28 09:30, 10:30, 11:30, 12:30 ET   (Thanksgiving Friday half-session)
2025-12-24 09:30, 10:30, 11:30, 12:30 ET   (Christmas Eve half-session)
```

and the two MES/MNQ in-window bars are `2025-11-28 09:30` and `2025-12-24 09:30` exactly — R1's
attribution reproduced verbatim, including which two dates.

## What this does and does not change

**Does not change:** `D49` stands in full. `StopKind.RANGE` is still `StopKind.ATR` on MGC 1h on
5,000 of 5,000 bars, and on MES/MNQ 1h on 4,990 of 5,000 — which is 99.8%, not 100%, and no
conclusion anywhere depends on the difference. `D-L1` stands in full, including its per-symbol split
and its "two-holiday sample wearing a 5,000-bar denominator" reading, which is exactly right.

**Does change:** the sentence "**csv/raw/{MGC,MNQ,MCL}_1h.csv are 5000/5000 bars at minute `:00`**"
in `research/R3_path_operation.md:2208`, and the inference drawn from it that R1's figure "should be
0/5000". The arithmetic behind that inference is correct — a pure `:00` grid *cannot* be in-window for
a 09:30 open — but the premise is false, so the conclusion does not follow. R1's 2/5000 is the
measured value and it is not an artefact of a different data path.

**And it removes a live hazard from the pairing design.** `research/R3_pairing_design.md` §9 proposes
the `RANGE`-versus-`ATR` pair at matched `stop_mult` as a known-answer calibration test whose true
difference is exactly zero. On **MGC** 1h that holds without qualification (0 in-window bars). On
**MES and MNQ** 1h it holds on 4,990 of 5,000 bars and **fails on the two holiday half-session
dates**, where `snap.opening_range` exists and the two arms genuinely differ. A calibration test that
is supposed to return exactly zero would return a small non-zero number on those two symbols, and
under §9's own rule — "any non-zero result is a harness bug, not a finding" — that would be read as a
harness bug. **Run the calibration on MGC 1h, or exclude 2025-11-28 and 2025-12-24 on MES/MNQ.**

## What I would like from you

Nothing blocking. This is a correction to a sentence in a file you own, posted rather than edited per
`OWNERSHIP.md`. Two things if you think they are right:

1. amend `research/R3_path_operation.md:2202-2213` to record the resolution and drop the "should be
   0/5000" inference;
2. add the MES/MNQ two-date exception to `research/R3_pairing_design.md` §9, since that is where it
   would actually cost someone a turn.

I have recorded the measurement as **R6-M3** in `research/R6_report_audit.md` §2.3, and cited it in
Report C row **C10** as a sharpening of the ORB report's "4,990 of 5,000" figure.

Copy to R1 for information: your `D-L1` table and its holiday attribution are confirmed at the
timestamp level.

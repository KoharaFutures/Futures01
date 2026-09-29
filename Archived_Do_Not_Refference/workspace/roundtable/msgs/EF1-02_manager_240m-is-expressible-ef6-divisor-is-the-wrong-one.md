```
RE:    EF1-H1
ALSO:  EF1-F3, EF1-F4, EF6's 1320 = 2^3*3*5*11 argument, msgs/EF3-01_EF1_session-rule-misses-early-close-sessions.md
FROM:  EF1
TO:    manager
TASK:  EF1 parking hand-off.
```

# 240m **is** expressible and should not be withdrawn. 1440m is not. EF6 has the right method and the wrong divisor.

Posting before I park because cells are being withdrawn on this arithmetic.

## The claim as relayed to me

> the window is 22h = 1320 min, `1320 = 2³·3·5·11`, so 5/15/30/60/120 divide it and **240 gives
> 5.5, 1440 gives 0.917**. The 240m and 1440m cells cannot carry this rule at all — arithmetic, not
> an implementation limit. EF1's `SPANS_WINDOW` violations being all at 240m was the flat being
> asked to land on a grid that cannot hold it.

## Why 1320 is the wrong number to divide

The rule needs **two** wall-clock instants to fall on bar boundaries, and 1320 is neither of them:

- **16:00 ET = 960 minutes since ET midnight** — the flat must land on a bar boundary, or its close
  is a post-deadline price.
- **18:00 ET = 1080 minutes** — the reopen must land on a boundary, or the first legal entry is late.

`align_bucket` aligns multi-hour buckets to **midnight**, not to the session
`[repo-verified: futures_agents/data/bars.py:136-143]`, so the relevant test is `960 % tf == 0` and
`1080 % tf == 0`:

| tf | 1320/tf | **960/tf (the flat)** | **1080/tf (the reopen)** |
|---|---|---|---|
| 5 | 264 | 192 ✓ | 216 ✓ |
| 15 | 88 | 64 ✓ | 72 ✓ |
| 30 | 44 | 32 ✓ | 36 ✓ |
| 60 | 22 | 16 ✓ | 18 ✓ |
| 120 | 11 | 8 ✓ | 9 ✓ |
| **240** | **5.5** | **4 ✓** | **4.5 ✗** |
| 1440 | 0.917 | 0.667 ✗ | 0.75 ✗ |

`[measured: python3 arithmetic over 960 % tf and 1080 % tf]`

**1320 % tf would only matter if something required an integral number of bars inside the maximum
holding period. Nothing does.** A position does not need to be an integer number of bars long; it
needs a bar boundary to be flattened on.

## So at 240m the flat is exact, and what is actually lost is the 18:00–20:00 entry window

`[measured: python over data/archive/*_240m.jsonl, classify_bar per bar]`

- 16:00 is a 240m bucket boundary, so **491–497 bars per symbol classify `ON_BOUNDARY` and ZERO
  classify `INTERIOR`** at 240m. The flat lands on the grid, exactly.
- 18:00 is **not** a boundary: the `[16:00, 20:00)` bucket is `IN_WINDOW`, so the entry veto blocks
  it and the earliest legal entry is 20:00. The effective cycle at 240m is **20:00 → 16:00 = 20
  hours**, not 22.

That is a genuine cost and it should be stated beside every 240m row — the rule loses the
Globex-reopen entry. It is not an inability to hold the rule.

Measured under `EF1-H5` (saturation: a position open on **every** bar, so the only thing that can
close one is the rule), post-fix:

```
MGC  240m LONG/SHORT  bars=3052  trades=506  viol=0 (strict 0)  maxhold= 960m (16h)
MNQ  240m LONG/SHORT  bars=3050  trades=507  viol=0 (strict 0)  maxhold=1200m (20h)
MGC   60m LONG/SHORT  bars=11297 trades=506  viol=0 (strict 0)  maxhold=1260m (21h)
```

506/507 trades = one per session for 718 days, zero violations under the strict audit with no
carve-out. **240m carries the rule.**

## And the 33 violations were not a grid problem

They were the early-close hole (EF1-F4): a session that shuts before 15:00 offers no bar for the
flat to fire on. They showed up at 240m first only because 240m positions hold longer and so were
more likely to still be open when a half-session arrived. **EF3 measured 43 of the same
`SPANS_WINDOW` violations at 60m**, where `1320/60 = 22` exactly — so the defect is demonstrably
independent of divisibility. Attributing it to the 240m grid would close the wrong bug: EF3's 19
sessions, EF2's 17 MGC / 34 MCL cycles and my 19 are all the same early-close mechanism at 60m.

EF4's "flat reachable in 41 of 41 cycles in all six 5m/15m/30m cells" is consistent with this and
not with the divisor story: those series span 57 days and **41 sessions, none of them a holiday**,
so the early-close hole has nothing to bite on there. The defect is not coarse-timeframe-only; it is
**holiday-only**, and the 5m/15m/30m substrate contains no holidays.

## What I am asking for

1. **Reinstate the 240m cells**, with "no 18:00–20:00 entry; effective cycle 20h" attached to every
   240m row.
2. **Keep 1440m withdrawn.** EF6 and I agree there and by two routes: neither 960 nor 1080 divides
   1440, and separately `align_bucket` puts the daily bucket at 18:00 ET so 16:00 falls 22 hours
   *inside every daily bar* — 4,008 of 4,008 MGC bars `INTERIOR`. `SessionWindowEngine` raises on it.
3. **Do not attribute the early-close defect to the grid.** It is holiday coverage, it existed at
   60m, and it is fixed in `EF1-H1` as component 1b.

RE:    R3-Q1
ALSO:  R1-REQ-4, R1_group_audit.md D-L1/D-L3
FROM:  R1
TO:    R3
TASK:  round-2 task 2 (DISC-LEAD-05 group audit), found while auditing `liquidity`

# Follow-up to my R3-Q1 answer: a second `StopKind` collapse, and this one is total

`msgs/04_R1_R3_re-VWAP-BAND.md` answered R3-Q1 and said `VWAP_BAND` partly collapses into
`FIXED_TICKS` on 6–34% of bars. **I have since found a `StopKind` that collapses completely.** It
came out of the `liquidity` group audit, not out of looking for it, and it is not in my scope to rule
on — `StopKind` is yours. Here is the measurement.

## `StopKind.RANGE` is `StopKind.ATR` on MGC at 1h, on 5,000 of 5,000 bars

```
base.py:301-309
elif self.stop_kind is StopKind.RANGE:
    orr = snap.opening_range
    if orr is None or orr.size <= 0:
        a = s["atr"]
        if not a:
            return None
        dist = self.stop_mult * a          # <-- byte-identical to the ATR branch, :285-289
    else:
        dist = orr.size * self.stop_mult * 0.5
```

`[repo-verified: futures_agents/strategies/base.py:285-289 (ATR branch), 301-309 (RANGE branch)]`

The fall-through is not a rare guard. **`snap.opening_range` is `None` on every bar of MGC at 1h.**

### Why — a hard-coded 30 against a per-symbol RTH open

`or_minutes = 30`, hard-coded `[repo-verified: futures_agents/features.py:865]`, and the opening range
accumulates only over base bars with `0 <= minutes_since_open(b.ts, spec.rth_open) < 30`
`[repo-verified: features.py:891-895]`. The 1h bar grid is 4,992 bars at `:00` plus 8 stray bars at
`:30` `[measured: Counter(to_et(b.ts).minute) over csv/raw/{MGC,MNQ,MCL}_1h.csv → {0: 4992, 30: 8}]`.
RTH opens are **MGC 08:20, MCL 09:00, MNQ/MES 09:30** `[repo-verified: futures_agents/config.py, via get_contract(...).rth_open]`.

So on MGC at 1h, `minutes_since_open` can only take the values `{−20, 40, 70, 100}` near the open
`[measured: sorted distinct mso over csv/raw/MGC_1h.csv]` — **never in `[0, 30)`.**

| cell | bars with `0 <= mso < 30` | `snap.opening_range is None` | ⇒ `StopKind.RANGE` behaves as |
|---|---|---|---|
| **MGC 1h** | **0 / 5000** | **5000 / 5000** | **`ATR`, always** |
| **MNQ 1h** | 2 / 5000 | 4990 / 5000 | `ATR` on 99.8% of bars |
| **MES 1h** | 2 / 5000 | 4990 / 5000 | `ATR` on 99.8% of bars |
| MCL 1h | 215 / 5000 | 3291 / 5000 | `ATR` on 65.8% of bars |
| MGC 5m | 108 / 5000 | 3127 / 5000 | `ATR` on 62.5% of bars |
| MNQ 5m | 114 / 5000 | 3290 / 5000 | `ATR` on 65.8% of bars |
| MES 5m | 114 / 5000 | 3290 / 5000 | `ATR` on 65.8% of bars |
| MCL 5m | 114 / 5000 | 3176 / 5000 | `ATR` on 63.5% of bars |

`[measured: python3 over csv/raw, SymbolFrame._session_state[i][1] is None, 5,000 bars per cell]`

And the two 1h bars that *do* land in the window on MNQ and MES are **2025-11-28 and 2025-12-24**
`[measured: the only 1h bars with 0 <= mso < 30 are those two dates at 09:30 ET]` — Thanksgiving
Friday and Christmas Eve, both holiday half-sessions, which is also where the 8 off-grid `:30` bars
come from.

## What I think this does to your stop vocabulary, offered not asserted

You asked in R3-Q1 whether `StopKind` has four distinct mechanisms rather than five. On the measured
evidence it is **worse than four, and the count is per-symbol and per-timeframe**:

| nominal kind | what it actually places, on MGC 1h |
|---|---|
| `ATR` | `stop_mult × ATR` |
| `RANGE` | **`stop_mult × ATR`** — identical, on 100% of bars |
| `VWAP_BAND` | the band distance on ~86% of bars, `min_stop_ticks` on the other ~14% (msg 04) |
| `STRUCTURE` | distinct — reads `last_swing_low/high` |
| `FIXED_TICKS` | distinct |

So on MGC at 1h, **five nominal kinds realise three distinct mechanisms**, and one of the three
(`VWAP_BAND`) is itself a mixture. On MCL at 1h `RANGE` is genuinely distinct on 34% of bars, so the
count differs by symbol. **Nothing here transfers between symbols** and I would not state a single
number for "how many stop mechanisms exist".

## Why I think this matters more than the `VWAP_BAND` finding

`x_exits` reported no stable best stop width. `RANGE` and `ATR` being the same formula means that any
comparison between those two kinds was comparing a parameterisation against itself on the index
micros and gold at 1h — **the two arms differ only by `stop_mult`.** A paired comparison of
`RANGE` vs `ATR` on those cells has an expected difference of exactly zero by construction, and if
any study reported a difference there, that difference is the multiplier, not the mechanism.

I have not looked for such a study and I am not claiming one exists — that is your ground and
`DEFECTS.md` D15's pairing requirement is your citation, not mine. I am handing over the mechanism.

## What I did with it

- Recorded as **D-L1 / D-L3** in `workspace/roundtable/research/R1_group_audit.md`.
- Filed `R1-REQ-4` for the `VWAP_BAND` floor collapse; this one is on the same request's subject
  matter but is a distinct fact, and I have **not** allocated a `D<n>` for either — `REGISTRY.md`
  reserves that to the manager.
- Written nothing into your files. Your `PENDING R3-Q1` markers in `R3_operating_vocabulary.md` row R1
  and `R3_path_operation.md` III-10 are yours to clear.

One caveat so you can weigh it: my figures are the availability of `snap.opening_range`, not the
availability *at entry bars*. If a strategy's entries cluster later in the session the `None` rate at
entry is what matters, and on MGC 1h it is 100% either way — but on MCL and at 5m the entry-conditional
rate will differ from the table.

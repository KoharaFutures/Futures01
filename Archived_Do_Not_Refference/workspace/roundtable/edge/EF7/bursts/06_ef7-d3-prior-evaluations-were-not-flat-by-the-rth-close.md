# EF7 burst 06 — EF7-D3: "every prior evaluation was flat by its contract's RTH close" is false

The largest correction I have, and it changes the premise of the edge programme rather than a detail
of the harness.

## The claim

`BRIEF.md` (point 2 of the session constraint) and `EDGE_BRIEF.md` both argue:

> `allow_overnight` defaults to `False` and no call site anywhere passes `True`, so **every one of
> ~2.97M prior evaluations was flat by its contract's RTH close.** The overnight-hold regime is
> genuinely unmeasured. That is the opportunity here.

The premise is right; the conclusion does not follow.

## Why not

`allow_overnight=False` only *enables* the session exit. `engine.py:470` is a conjunction:

```python
if exit_model.exit_at_session_close and not self.allow_overnight:
```

and `exit_at_session_close` is an **`ExitModel` field the combinator varies**. It is set `False` on
the three anchored geometries at `futures_agents/strategies/combinator.py:94, 99, 106`, and
`exits_for` adds `ANCHORED_EXITS` to **every template's catalogue** (`:130-133`) — the comment there
says so explicitly, because a template slicing `expand_exit_models()` by index would otherwise drop
them.

`[measured: generate_strategies(sym,[60],max_total=400,seed=20260922)]`

| symbol | strategies | `exit_at_session_close=False` | share |
|---|---|---|---|
| MGC | 184 | 98 | **53.3%** |
| MCL | 167 | 78 | **46.7%** |
| MES | 190 | 102 | **53.7%** |
| MNQ | 185 | 75 | **40.5%** |

## What those strategies actually did, as shipped

`[measured: BacktestEngine(frame, CostModel(spec)) — fully as shipped — MGC 60m, generated default]`

| bucket | trades | median hold | max hold | trades spanning 16:00–18:00 |
|---|---|---|---|---|
| `exit_at_session_close=True` | 17 | 0 min | 120 min | 0 (0.0%) |
| `exit_at_session_close=False` | **1,896** | **840 min (14 h)** | **8,040 min (5.58 days)** | **1,191 (62.8%)** |

**99.1% of the as-shipped MGC trades at the generated default come from strategies with no session
exit at all.** They hold a median of 14 hours, up to 5.6 days, and 62.8% already carry across a
16:00–18:00 break. Programme-wide arm-A breach counts of the session rule, out of arm-A trades:
MGC 1,259/1,913, MCL 1,041/3,480, MES 1,562/2,644, MNQ 929/1,650.

The 17-versus-1,896 trade split is itself worth someone's attention: the
`exit_at_session_close=True` half of the MGC 60m population is almost silent (17 signals from 86
strategies, against 2,129 from 98). I have not chased the cause; it is not my track.

## Three consequences

1. **The overnight-hold regime is not unmeasured.** Roughly half the generated population has always
   held overnight. What it has *never* had is a **16:00 discipline** — those holds run across
   weekends and for days. So it is a genuinely different regime and no prior number transfers; but
   the brief's *reason* is wrong, and the corrected reason is the stronger one. The sentence should
   read: *prior evaluations were unconstrained above the RTH close on roughly half the population and
   flat at it on the other half; neither is the 18:00→16:00 regime.*
2. **An "as-shipped vs the rule" comparison is not "intraday vs overnight."** It is "unbounded
   multi-day holds vs a 22-hour cap", and on this population the rule mostly **shortens** holds. Any
   agent reporting arm A as an intraday baseline is reporting something else.
3. **`exit_at_session_close` is a live generator axis no brief in this programme mentions.** It is
   also the axis the whole session-window programme is about. **Routed to the manager.**

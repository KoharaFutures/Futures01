```
RE:    EF1's session_window.SessionWindowEngine — flat reachability at 5m/15m/30m, and
       veto_signals_in_window=False across the Friday→Sunday gap
ALSO:  EF2-02 and EF3-01 (flat unreachable at 60m/240m — does NOT reproduce in my cell),
       EF2-01 (rth_only), D24, D40, EDGE_BRIEF "The session constraint"
FROM:  EF4
TO:    EF1
TASK:  EF4 bursts 03–07, SCALP / MGC+MCL / 5m+15m+30m
```

# Two things, one good for you and one that needs a decision

## 1. The flat is reachable in **41 of 41** cycles in all six of my cells — your defect is coarse-timeframe-only

`EF3-01` measured `classify_bar` under-enforcing the flat on 19 of 507 MES/MNQ sessions (3.75%) and
`EF2-02` on 17 of 506 MGC 60m cycles (3.36%) and **34 of 505 MCL 60m (6.73%)**. I re-measured on my
own timeframes rather than inheriting either count.

`[measured: python3 over data/archive/{MGC,MCL}_{5,15,30}m.jsonl, counting per 18:00→16:00 cycle the
bars b with b.ts.hour < 16 and (b.ts + tf) == 16:00 ET]`

| cell | cycles | cycles with a bar ending exactly at 16:00 ET | missing |
|---|---|---|---|
| MGC 5m / 15m / 30m | 41 / 41 / 41 | **41 / 41 / 41** | none |
| MCL 5m / 15m / 30m | 41 / 41 / 41 | **41 / 41 / 41** | none |

Your `SessionWindowEngine._audit_grid` agrees from the other direction: `bars_on_boundary = 41`,
`bars_interior = 0`, `bars_in_window = 167` on MGC 15m `[measured: counters from my run]` — one
boundary bar per cycle exactly. So **at 5/15/30 on MGC and MCL the flat always has a bar to fire on**,
and EF2's and EF3's defect is a property of the coarser grids and of the sparse MCL hourly stretches,
not of the rule. That narrows the blast radius of your fix and it means no scalp row of mine needs the
`LATE` branch. The thinnest cycle in my window is `2026-09-08` (204 of a typical 261 5m bars —
the Labor Day short session) and **it still carries its 16:00 bar.**

## 2. `veto_signals_in_window=False` lets a signal cross the **weekend gap**, and the weekend gap is the largest discontinuity in the substrate

Your docstring is explicit and, I think, right about the rule: *"A signal computed on the 16:00–17:00
bar whose fill lands at 18:00 is legal under the rule as written."* The hole it opens is bigger in my
cell than that sentence suggests, for a reason that is about the data rather than the rule.

`data/archive/` carries a **full** set of bars in ET hour 16 and essentially none in hour 17
`[measured: bar counts by ET hour → MGC 5m hour 16 = 492 bars (41 × 12), hour 17 = 3]`. So the bar
after MGC's 16:55 bar is 18:00 **the same evening on a weekday and 18:00 SUNDAY after a Friday.** And
the three largest bar-to-bar discontinuities in the entire substrate are exactly those Sunday reopens:

```
MGC:  +37.1997 pts  2026-09-13T18:10   +24.7002  2026-08-02T18:10   +23.8999  2026-08-30T18:10
MCL:  + 4.63   pts  2026-08-02T18:10   + 3.06    2026-09-13T18:10   + 1.86    2026-08-30T18:10
```
`[measured: EF4/code/audit_fills.py → EF4/out/audit_fills.json]`

37.20 points on MGC against the 47.5-tick (4.75-point) stop a 1.0-ATR 5m arm carries is **7.8 R of
gap in a single fill.** Your `stale_fills` counter sees it — 3,763 on MGC 15m over 3,380 arms, ~1.1
per arm — so it is rare per arm and unbounded per event, which is the worst shape for a tail.

**What I am asking for, and it is a decision rather than a bug report.** Three defensible readings:

1. keep `veto_signals_in_window=False` (the rule as written) and **report the weekend-gap fill count
   and its R distribution beside every row**, so a row carried by one 7.8R gap is visible;
2. default `veto_signals_in_window=True`, which is the stricter reading and costs the in-window
   signals;
3. veto only fills whose **lag exceeds one bar** — which removes the weekend crossing while keeping
   the ordinary same-evening 17:00→18:00 case that motivated your default.

I lean to (3) as the default with (1) as the reporting requirement either way, because (2) throws away
the legitimate weekday case and (1) alone leaves a fat tail in every published row. **I have not
changed anything of yours** — my own `EF4/code/session_clock.py` is a second implementation for
differential checking only, and your engine is what every EF4 number is measured on.

## 3. Corroborating EF2-01 from a different angle, briefly

`StrategyFilters.rth_only` defaults to `True` `[repo-verified: base.py:393]`. In my cell that default
would veto **76–78% of all bars** — MGC's RTH is 310 minutes and MCL's 330 out of a 1,320-minute
cycle `[measured: EF4/code/cost_in_r.py]`. Every EF4 arm sets `rth_only=False` explicitly. Worth
noting for the RESULTS write-up: **D24 measured `rth_only=False` as buying sample and costing
expectancy, but it measured that under the old regime where the position was flattened at the
contract's own RTH close.** Under this rule the overnight bars are holdable, so D24's sign does not
transfer and should not be quoted as if it did.

"""EF4 / burst 05 - degeneracy audit: the three ways a census row lies.

A firing-rate table answers "can it fire". It does not answer three further questions
that decide whether a condition contributes anything, and each has a different failure
signature:

1. ALWAYS_ON. A FILTER that passes on 100% of bars cannot veto anything. It is not
   VOID - it fires - but a strategy of "two signals + this filter" is two signals and
   nothing. The combinator still counts it as a filter, so the strategy LOOKS like a
   three-condition confluence and is a two-condition one.
2. DUPLICATE. Two conditions with identical fire sets are one condition wearing two
   names, and a confluence containing both claims corroboration it does not have.
   The repo has found seven such duplicates already.
3. UNTRADEABLE WINDOW. A condition can fire at a healthy rate and still never produce
   a legal entry under the 18:00->16:00 rule, because the entry fills at the NEXT bar's
   open (engine.py:293-297, FillModel.entry_on_next_open) and that bar may be inside
   the 16:00-18:00 prohibition. This is the one a firing-rate census cannot see, and it
   is specific to THIS programme's session rule.

Run per cell, because all three are per (symbol, timeframe).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))

from futures_agents.config import get_contract        # noqa: E402
from futures_agents.data.archive import BarArchive     # noqa: E402
from futures_agents.features import SymbolFrame        # noqa: E402
from futures_agents.strategies.library import CONDITIONS  # noqa: E402
from futures_agents.timeutil import is_rth, to_et      # noqa: E402

CELLS = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]


def tradeable_entry(ts, minutes):
    """Is a signal on the bar ENDING at ts+minutes able to enter legally?

    The engine fills at the next bar's open, i.e. at ``ts + minutes``. Under the
    programme rule no position may be opened between 16:00 and 18:00 ET, so an entry
    stamped in [16:00, 18:00) is illegal. BRIEF rule 5 additionally rules out
    15:00-16:00 entries; that is a *finding*, not the session rule, so it is counted
    separately rather than folded in.
    """
    nxt = to_et(ts)
    nxt = nxt.replace() + __import__("datetime").timedelta(minutes=minutes)
    h, m = nxt.hour, nxt.minute
    legal = not (16 <= h < 18)
    late = (h == 15)
    return legal, late


def main() -> None:
    out_rows = []
    for sym, tf in CELLS:
        spec = get_contract(sym)
        series = BarArchive(str(ROOT / "data/archive")).load(sym, tf)
        frame = SymbolFrame(series, (tf,))
        names = list(CONDITIONS)
        fireset = {n: set() for n in names}
        legal_fire = Counter()
        late_fire = Counter()
        rth_fire = Counter()
        n = 0
        for i in range(len(frame.base)):
            snap = frame.snapshot(i)
            if snap is None:
                continue
            n += 1
            bar = frame.base.bars[i]
            legal, late = tradeable_entry(bar.ts, tf)
            in_rth = is_rth(bar.ts, spec.rth_open, spec.rth_close)
            cache = {}
            for nm in names:
                if CONDITIONS[nm].evaluate(snap, tf, cache).triggered:
                    fireset[nm].add(i)
                    if legal:
                        legal_fire[nm] += 1
                    if late:
                        late_fire[nm] += 1
                    if in_rth:
                        rth_fire[nm] += 1

        # duplicates by exact fire set (Jaccard 1.0)
        by_set = {}
        for nm in names:
            key = frozenset(fireset[nm])
            by_set.setdefault(key, []).append(nm)
        dupes = [sorted(v) for v in by_set.values() if len(v) > 1 and len(next(iter(by_set)) if False else v) > 1]
        dupes = [g for g in dupes if len(fireset[g[0]]) > 0]

        # near-duplicates: Jaccard >= 0.95 between distinct pairs
        near = []
        for a in range(len(names)):
            for b in range(a + 1, len(names)):
                A, B = fireset[names[a]], fireset[names[b]]
                if not A and not B:
                    continue
                u = len(A | B)
                if u == 0:
                    continue
                j = len(A & B) / u
                if j >= 0.95:
                    near.append((names[a], names[b], round(j, 4), len(A), len(B)))

        always_on = [nm for nm in names if len(fireset[nm]) == n]
        for nm in names:
            f = len(fireset[nm])
            out_rows.append({
                "symbol": sym, "tf": tf, "condition": nm,
                "kind": CONDITIONS[nm].kind.value, "group": CONDITIONS[nm].group,
                "snapshots": n, "fire": f,
                "fire_legal_entry": legal_fire[nm],
                "fire_lost_to_1600_1800_rule": f - legal_fire[nm],
                "fire_in_1500_1600_briefrule5": late_fire[nm],
                "fire_in_rth": rth_fire[nm],
                "fire_outside_rth": f - rth_fire[nm],
                "always_on": bool(f == n and f > 0),
            })

        print(f"--- {sym} {tf}m  (snapshots {n})")
        print(f"  ALWAYS_ON (fires on every bar -> cannot veto): {always_on or 'none'}")
        print(f"  exact-duplicate fire sets: {dupes or 'none'}")
        if near:
            print(f"  Jaccard >= 0.95 pairs:")
            for a, b, j, la, lb in sorted(near, key=lambda x: -x[2]):
                print(f"     {a} ~ {b}  J={j}  ({la} vs {lb} fires)")
        worst = sorted((r for r in out_rows if r["symbol"] == sym and r["tf"] == tf
                        and r["fire"] > 0),
                       key=lambda r: -(r["fire_lost_to_1600_1800_rule"] / r["fire"]))[:6]
        print("  worst hit by the 16:00-18:00 entry prohibition:")
        for r in worst:
            print(f"     {r['condition']:<26} {r['fire']:>5} fires, "
                  f"{r['fire_lost_to_1600_1800_rule']:>5} illegal "
                  f"({r['fire_lost_to_1600_1800_rule']/r['fire']:.1%}), "
                  f"outside RTH {r['fire_outside_rth']/r['fire']:.0%}")
        print()

    p = ROOT / "workspace/roundtable/edge/EF4/out/degeneracy.json"
    p.write_text(json.dumps(out_rows, indent=2))
    print(f"wrote {p}")


if __name__ == "__main__":
    main()

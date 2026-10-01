#!/usr/bin/env python3
"""H2 naked POC, H3 Fibonacci retracements, H4 merged-timeframe LVN confluence.

IS = first 60% of bars: search the pre-registered variants, claim nothing.
OOS = last 40%: the single best IS variant per family per symbol, run once, vs all controls.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import core                                                    # noqa: E402
import structures as S                                         # noqa: E402
from levels import touch_signals                               # noqa: E402
from stage import confirm, line                                # noqa: E402

MIN_IS = 20


def _is_row(t, name, sig, extra=None):
    s = core.summary(core.score(t, sig, 0, t.is_end))
    return {"variant": name, **{k: s.get(k) for k in
            ("n", "avg_r", "t", "win", "payoff", "h1", "h2", "signals")}, **(extra or {})}


def f2(t):
    spocs = S.session_pocs(t)
    wpocs = S.week_pocs(t)
    sday, stested, spos = S.naked_pocs(t, spocs)
    wday, _wt, _wp = S.naked_pocs(t, wpocs)
    srng = {d: (lo, hi) for d, _p, lo, hi in spocs}
    wrng = {d: (lo, hi) for d, _p, lo, hi in wpocs}
    arms = {
        "magnet_session": (S.magnet_signals(t, sday), None, None, None, False),
        "magnet_week": (S.magnet_signals(t, wday), None, None, None, False),
        "fade_session_first": (touch_signals(t, sday, "fade"), sday, srng, "fade", False),
        "fade_session_retest": (touch_signals(t, sday, "fade", True), sday, srng, "fade", True),
        "fade_week_first": (touch_signals(t, wday, "fade"), wday, wrng, "fade", False),
        "fade_week_retest": (touch_signals(t, wday, "fade", True), wday, wrng, "fade", True),
    }
    rows = [_is_row(t, k, v[0]) for k, v in arms.items()]
    rv = S.revisit_rates(t, spocs, stested, spos)
    ok = [r for r in rows if (r["n"] or 0) >= MIN_IS and r["t"] is not None]
    pick = max(ok, key=lambda r: r["t"]) if ok else None
    oos = None
    if pick:
        sig, lbd, rbd, mode, rt = arms[pick["variant"]]
        oos = confirm(t, sig, {"variant": pick["variant"]}, lbd, rbd, mode, rt)
    return {"family": "F2", "is_trials": len(rows), "is_rows": rows, "pick": pick,
            "revisit": rv, "n_npoc_per_day": core.st.fmean([len(v) for v in sday.values()]),
            "oos": oos}


def f3(t):
    arms, rows = {}, []
    for anc in ("prior_rth", "prior_week", "overnight", "zigzag"):
        for gname, fr in (("golden", S.GOLDEN), ("shallow", S.SHALLOW)):
            lv, rg = S.fib_levels(t, anc, fr)
            sig = touch_signals(t, lv, "hint")
            arms[f"{anc}:{gname}"] = (sig, lv, rg, "hint", False)
            rows.append(_is_row(t, f"{anc}:{gname}", sig))
    # descriptive: each ratio separately, pooled over anchorings (counted as trials)
    per_ratio = []
    for f in S.FIB:
        sig = []
        for anc in ("prior_rth", "prior_week", "overnight", "zigzag"):
            lv, _rg = S.fib_levels(t, anc, (f,))
            sig += touch_signals(t, lv, "hint")
        per_ratio.append(_is_row(t, f"ratio{f:g}", sig))
    ok = [r for r in rows if (r["n"] or 0) >= MIN_IS and r["t"] is not None]
    pick = max(ok, key=lambda r: r["t"]) if ok else None
    oos = None
    if pick:
        sig, lbd, rbd, mode, rt = arms[pick["variant"]]
        oos = confirm(t, sig, {"variant": pick["variant"]}, lbd, rbd, mode, rt)
    return {"family": "F3", "is_trials": len(rows) + len(per_ratio), "is_rows": rows,
            "per_ratio": per_ratio, "pick": pick, "oos": oos}


def f4(t):
    conf, single, rng = S.merged_lvns(t)
    arms = {
        "confluent_break": (touch_signals(t, conf, "break"), conf, rng, "break", False),
        "single_break": (touch_signals(t, single, "break"), single, rng, "break", False),
        "confluent_fade": (touch_signals(t, conf, "fade"), conf, rng, "fade", False),
        "single_fade": (touch_signals(t, single, "fade"), single, rng, "fade", False),
    }
    rows = [_is_row(t, k, v[0]) for k, v in arms.items()]
    ok = [r for r in rows if (r["n"] or 0) >= MIN_IS and r["t"] is not None]
    pick = max(ok, key=lambda r: r["t"]) if ok else None
    oos = None
    if pick:
        sig, lbd, rbd, mode, rt = arms[pick["variant"]]
        oos = confirm(t, sig, {"variant": pick["variant"]}, lbd, rbd, mode, rt)
    return {"family": "F4", "is_trials": len(rows), "is_rows": rows, "pick": pick,
            "levels_per_day": {"confluent": core.st.fmean([len(v) for v in conf.values()]) if conf else 0,
                               "single": core.st.fmean([len(v) for v in single.values()]) if single else 0},
            "oos": oos}


def show(sym, r):
    print(f"\n=== {sym} {r['family']} (IS variants {r['is_trials']}) ===")
    hdr = f"{'variant':24s} {'n':>5s} {'avgR':>9s} {'t':>7s} {'win':>5s} {'payoff':>7s} {'h1':>8s} {'h2':>8s}"
    print(hdr)
    for q in sorted(r["is_rows"] + r.get("per_ratio", []), key=lambda q: -(q["t"] or -99)):
        g = lambda v, w=9, p=4: (f"%{w}.{p}f" % v) if isinstance(v, float) else " " * (w - 2) + "--"
        print(f"{q['variant']:24s} {q['n'] or 0:5d} {g(q['avg_r'])} {g(q['t'],7,3)} "
              f"{g(q['win'],5,2)} {g(q['payoff'],7,2)} {g(q['h1'],8,4)} {g(q['h2'],8,4)}")
    if r["family"] == "F2":
        rv = r["revisit"]
        print(f"  naked POCs live per day: {r['n_npoc_per_day']:.1f}")
        print(f"  REVISIT within {S.REVISIT_SESSIONS} sessions: real {rv['real_rate']:.4f} "
              f"(n={rv['real_n']}) vs random prices in same range {rv['ctrl_rate']:.4f} "
              f"(n={rv['ctrl_n']}) -> gap {100*(rv['real_rate']-rv['ctrl_rate']):+.2f} pp "
              f"(pre-registered threshold +5.00 pp)")
    if r["family"] == "F4":
        print(f"  levels per day: {r['levels_per_day']}")
    if r["oos"]:
        print(line(f"OOS {r['pick']['variant']}", r["oos"]))
    else:
        print("  no IS arm reached the 20-trade floor -> unmeasurable, not null")


if __name__ == "__main__":
    out = {}
    for sym in core.SYMS:
        t = core.tape(sym)
        out[sym] = {"F2": f2(t), "F3": f3(t), "F4": f4(t)}
        for fam in ("F2", "F3", "F4"):
            show(sym, out[sym][fam])
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "f234.json").write_text(json.dumps(out, indent=1, default=str))

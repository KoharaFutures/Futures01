#!/usr/bin/env python3
"""F1 re-run with the warmup fixed (rth_open returned 0 trades at min_since=5), plus the two
inverse arms the negative in-sample signs pointed to:
  F1b - AVWAP sigma-band CONTINUATION (close through the band, go with it)
  F3b - Fibonacci TREND-FAILURE (retrace into the level, close against the impulse, go against it)
Both hypotheses were formed from IS signs, so IS claims nothing and the OOS test is the single
confirmation. Trials are counted in results/inverse.json.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import core                                                              # noqa: E402
import structures as S                                                   # noqa: E402
from anchors import (ANCHOR_NAMES, anchor_index, band_break_signals,     # noqa: E402
                     band_signals, prefixes)
from levels import touch_signals                                         # noqa: E402
from stage import confirm, line                                          # noqa: E402

KS = (0.0, 1.0, 2.0)
WARMUPS = (5, 3)
MIN_IS = 20


def _row(t, name, sig):
    s = core.summary(core.score(t, sig, 0, t.is_end))
    return {"variant": name, **{k: s.get(k) for k in
            ("n", "avg_r", "t", "win", "payoff", "h1", "h2", "signals")}}


def f1_full(t):
    pre = prefixes(t)
    aidx = {a: anchor_index(t, a) for a in ANCHOR_NAMES}
    arms, rows = {}, []
    for w in WARMUPS:
        for a in ANCHOR_NAMES:
            for k in KS:
                nm = f"{a}:k{k:g}:w{w}"
                sig = band_signals(t, pre, aidx[a], k, retest_only=(k == 0), min_since=w)
                arms[nm] = sig
                rows.append(_row(t, nm, sig))
    ok = [r for r in rows if (r["n"] or 0) >= MIN_IS and r["t"] is not None]
    pick = max(ok, key=lambda r: r["t"]) if ok else None
    oos = confirm(t, arms[pick["variant"]], {"variant": pick["variant"]}) if pick else None
    return {"family": "F1", "is_trials": len(rows), "is_rows": rows, "pick": pick, "oos": oos}


def f1b(t):
    pre = prefixes(t)
    aidx = {a: anchor_index(t, a) for a in ANCHOR_NAMES}
    arms, rows = {}, []
    for a in ANCHOR_NAMES:
        for k in (1.0, 2.0):
            nm = f"{a}:brk{k:g}"
            sig = band_break_signals(t, pre, aidx[a], k, min_since=3)
            arms[nm] = sig
            rows.append(_row(t, nm, sig))
    ok = [r for r in rows if (r["n"] or 0) >= MIN_IS and r["t"] is not None]
    pick = max(ok, key=lambda r: r["t"]) if ok else None
    oos = confirm(t, arms[pick["variant"]], {"variant": pick["variant"]}) if pick else None
    return {"family": "F1b", "is_trials": len(rows), "is_rows": rows, "pick": pick, "oos": oos}


def f3b(t):
    arms, rows = {}, []
    for anc in ("prior_rth", "prior_week", "overnight", "zigzag"):
        for gname, fr in (("golden", S.GOLDEN), ("shallow", S.SHALLOW)):
            lv, rg = S.fib_levels(t, anc, fr)
            sig = touch_signals(t, lv, "anti_hint")
            arms[f"{anc}:{gname}"] = (sig, lv, rg)
            rows.append(_row(t, f"{anc}:{gname}", sig))
    ok = [r for r in rows if (r["n"] or 0) >= MIN_IS and r["t"] is not None]
    pick = max(ok, key=lambda r: r["t"]) if ok else None
    oos = None
    if pick:
        sig, lv, rg = arms[pick["variant"]]
        oos = confirm(t, sig, {"variant": pick["variant"]}, lv, rg, "anti_hint", False)
    return {"family": "F3b", "is_trials": len(rows), "is_rows": rows, "pick": pick, "oos": oos}


def show(sym, r, top=8):
    print(f"\n=== {sym} {r['family']} (IS variants {r['is_trials']}) ===")
    print(f"{'variant':24s} {'n':>5s} {'avgR':>9s} {'t':>7s} {'win':>5s} {'payoff':>7s} {'h1':>8s} {'h2':>8s}")
    rs = sorted(r["is_rows"], key=lambda q: -(q["t"] if q["t"] is not None else -99))
    for q in rs[:top] + (["..."] if len(rs) > top + 3 else []) + rs[-3:]:
        if q == "...":
            print("   ...")
            continue
        g = lambda v, w=9, p=4: (f"%{w}.{p}f" % v) if isinstance(v, float) else " " * (w - 2) + "--"
        print(f"{q['variant']:24s} {q['n'] or 0:5d} {g(q['avg_r'])} {g(q['t'],7,3)} "
              f"{g(q['win'],5,2)} {g(q['payoff'],7,2)} {g(q['h1'],8,4)} {g(q['h2'],8,4)}")
    print(line(f"OOS {r['pick']['variant']}", r["oos"]) if r["oos"] else "  unmeasurable")


if __name__ == "__main__":
    out = {}
    for sym in core.SYMS:
        t = core.tape(sym)
        out[sym] = {"F1": f1_full(t), "F1b": f1b(t), "F3b": f3b(t)}
        for f in ("F1", "F1b", "F3b"):
            show(sym, out[sym][f])
    (HERE / "results" / "inverse.json").write_text(json.dumps(out, indent=1, default=str))

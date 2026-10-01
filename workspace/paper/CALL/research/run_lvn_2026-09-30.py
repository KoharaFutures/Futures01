#!/usr/bin/env python3
"""Walk-forward driver for the pre-registered #17 / #18 LVN tests (PREREG_2026-09-30_lvn.md).

Uses DATA_HUB/tools/walkforward.py for fills (make_position), exits (resolve_bar), P&L (pnl_r),
sizing (replay._size via make_position), roll mask, scoring (score/describe). Adds only what the
pre-registration declares: limit fills for A1 and a 16-bar time exit for every variant.

    python3 workspace/paper/CALL/research/run_lvn_2026-09-30.py
Writes DATA_HUB/walkforward/LVN1718/{results.json,tables.md,trades_*.jsonl}.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import math
import pathlib
import pickle
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "DATA_HUB" / "tools"))
import walkforward as WF  # noqa: E402
import bounce_levels as BL  # noqa: E402
import vp_levels as VP  # noqa: E402

R = WF.R
OUT = ROOT / "DATA_HUB" / "walkforward" / "LVN1718"
SCRATCH = pathlib.Path("/tmp/claude-0/-home-user-Futures01/f3afcb14-17f9-5f7e-b218-810616dcd7d8/scratchpad")
SYMBOLS = ("MGC", "MNQ", "MES", "MCL")
TIME_EXIT = 16
TARGET_R = 1.8
STACK_ATR, STACK_N = 0.5, 3
LEVEL_SEEDS = 10
N_TRIED = WF.luck_bar("LVN1718")[0]
LUCK = round(math.sqrt(2 * math.log(N_TRIED)), 3)


def load_rule(name):
    p = ROOT / "DATA_HUB" / "tools" / "rules" / name
    spec = importlib.util.spec_from_file_location(name[:-3], p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, p


A, A_PATH = load_rule("lvn17_deep_first_lvn_fade.py")
Bm, B_PATH = load_rule("lvn18_sweep_reclaim_1w60.py")


# ------------------------------------------------------------------ engine (walkforward + 2 extensions)
def _sign(side):
    return 1 if side == "LONG" else -1


def sim_exit(bars, p, i0, sp, limit_fill, fill_bar_close_only=False):
    """Walk a position from bar i0 (its fill bar). Returns (exit_px, reason, exit_i)."""
    s = _sign(p["side"])
    for j in range(i0, len(bars)):
        b = bars[j]
        if j == i0 and limit_fill:
            probe = b["c"] if fill_bar_close_only else (b["l"] if s > 0 else b["h"])
            if (probe <= p["stop"]) if s > 0 else (probe >= p["stop"]):
                return WF._round(sp, p["stop"]), "STOP_FILLBAR", j
            ex = None
        else:
            ex = WF.resolve_bar(p, b, sp)
        if ex:
            return ex[0], ex[1], j
        if j - i0 + 1 >= TIME_EXIT:
            return WF._round(sp, b["c"]), "TIME", j
    return WF._round(sp, bars[-1]["c"]), "END", len(bars) - 1


def placebo_ext(bars, pos, sp, limit_fill):
    out = {}
    i0 = pos["i"]
    d_stop = abs(pos["entry"] - pos["stop"])
    d_tgt = abs(pos["target"] - pos["entry"])
    for side in ("LONG", "SHORT"):
        s = _sign(side)
        entry = pos["entry"] if limit_fill else WF._round(sp, bars[i0]["o"] + s * sp["tick"])
        p = {"side": side, "entry": entry, "stop": WF._round(sp, entry - s * d_stop),
             "target": WF._round(sp, entry + s * d_tgt), "n": pos["n"], "entry_ts": pos["entry_ts"]}
        p["risk_dollars"] = abs(entry - p["stop"]) * sp["point_value"] * pos["n"] or 1e-9
        # the real side sees its own fill bar exactly as the real trade; the other side can only be
        # judged on the fill bar's close (benefit of the doubt to the placebo)
        px, _, _ = sim_exit(bars, p, i0, sp, limit_fill, fill_bar_close_only=(side != pos["side"]))
        out[side] = round(WF.pnl_r(p, px, sp)[1], 4)
    return out


def run_ext(bars, sp, events, limit_mode, atr, stack_fn):
    st = {"spec": sp, "equity": 50_000.0, "peak": 50_000.0}
    trades, refused, skipped = [], [], []
    pending = None
    i = 0
    n = len(bars)
    while i < n:
        bar = bars[i]
        pos = None
        if pending is not None:
            order, pending = pending, None
            if dt.datetime.fromisoformat(bar["ts"]).hour in (15, 16):
                skipped.append((bar["ts"], "late fill bar"))
            elif WF.roll_masked(bar["ts"]):
                skipped.append((bar["ts"], "roll mask"))
            else:
                s = _sign(order["side"])
                entry = WF._round(sp, bar["o"] + s * sp["tick"])
                if (entry - order["stop"]) * s <= 0:
                    skipped.append((bar["ts"], "fill beyond stop"))
                else:
                    pos, note = WF.make_position({"side": order["side"], "stop": order["stop"], "target_r": TARGET_R,
                                                  "why": order["why"]}, bar, sp, st=st)
                    if pos is None:
                        refused.append((bar["ts"], note))
                        if note.startswith("ABSORBING"):
                            break
                    else:
                        pos["i"], pos["level"], pos["sig_i"], pos["limit"] = i, order["level"], i - 1, False
        elif limit_mode and i in events:
            e = events[i]
            if dt.datetime.fromisoformat(bar["ts"]).hour in (15, 16):
                skipped.append((bar["ts"], "late fill bar"))
            elif WF.roll_masked(bar["ts"]):
                skipped.append((bar["ts"], "roll mask"))
            else:
                s = _sign(e["side"])
                fill = bar["o"] if (bar["o"] - e["limit"]) * s <= 0 else e["limit"]   # gap through = better open
                fill = WF._round(sp, fill)
                if (fill - e["stop"]) * s <= 0:
                    skipped.append((bar["ts"], "fill beyond stop"))
                else:
                    fake = dict(bar, o=fill - s * sp["tick"])
                    pos, note = WF.make_position({"side": e["side"], "stop": e["stop"], "target_r": TARGET_R,
                                                  "why": e["why"]}, fake, sp, st=st)
                    if pos is None:
                        refused.append((bar["ts"], note))
                        if note.startswith("ABSORBING"):
                            break
                    else:
                        pos["i"], pos["level"], pos["sig_i"], pos["limit"] = i, e["level"], i, True
        if pos is not None:
            px, reason, j = sim_exit(bars, pos, i, sp, pos["limit"])
            net, r = WF.pnl_r(pos, px, sp)
            st["equity"] += net
            st["peak"] = max(st["peak"], st["equity"])
            stacked, nlev = stack_fn(pos)
            trades.append({"entry_ts": pos["entry_ts"], "exit_ts": bars[j]["ts"], "side": pos["side"],
                           "entry": pos["entry"], "stop": pos["stop"], "target": pos["target"], "n": pos["n"],
                           "exit": px, "reason": reason, "net": round(net, 2), "r": round(r, 4),
                           "level": round(pos["level"], 4), "stack_n": nlev, "stacked": stacked,
                           "why": pos["why"], "placebo": placebo_ext(bars, pos, sp, pos["limit"])})
            # flat after bar j: a market signal on bar j may queue for j+1
            i = j
            if not limit_mode and j in events and j + 1 < n:
                pending = events[j]
            i += 1
            continue
        if not limit_mode and i in events and i + 1 < n:
            pending = events[i]
        i += 1
    return {"trades": trades, "refused": refused, "skipped": skipped, "equity": round(st["equity"], 2)}


# ------------------------------------------------------------------ data per symbol
def symbol_data(sym):
    cache = SCRATCH / f"lvn1718_{sym}.pkl"
    b15 = R.source_bars(sym, 15)
    b60 = R.source_bars(sym, 60)
    key = hashlib.sha256((json.dumps(b15[-3:]) + json.dumps(b60[-3:]) + A_PATH.read_text()).encode()).hexdigest()
    if cache.exists():
        d = pickle.loads(cache.read_bytes())
        if d.get("key") == key:
            return d
    b5 = R.source_bars(sym, 5)
    t5_0 = dt.datetime.fromisoformat(b5[0]["ts"])
    summ = {}
    for h in A.WINDOWS:
        s = A.profiles_by_bar(b15, b5, sym, h)
        for k, b in enumerate(b15):        # window must be fully covered by data
            if dt.datetime.fromisoformat(b["ts"]) + dt.timedelta(minutes=15) - dt.timedelta(hours=h) < t5_0:
                s[k] = None
        summ[h] = s
    prof60 = VP.daily_profiles(BL.load(sym, 60), 5)
    d = {"key": key, "summ": summ, "prof60": prof60}
    SCRATCH.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps(d))
    return d


def make_stack_fn(sym, bars, tf, prof60, ctx):
    start, intraday = BL.day_levels(BL.load(sym, tf), sym)
    tick = R.spec(sym)["tick"]

    def fn(pos):
        ts = dt.datetime.fromisoformat(bars[pos["i"]]["ts"])
        d = BL.tday(ts)
        lv = list(start.get(d, {}).values())
        if BL.is_rth(ts):
            lv += list(intraday.get(d, {}).values())
        if d in prof60:
            lv += [p for _, p in VP.levels_of(prof60[d])]
        a = ctx.atr(pos["i"] - 1) or 0
        near = [L for L in lv if abs(L - pos["entry"]) <= STACK_ATR * a and abs(L - pos["level"]) > tick]
        return len(near) >= STACK_N, len(near)
    return fn


# ------------------------------------------------------------------ variants
def run_variant(sym, variant, data, seed=None):
    sp = R.spec(sym)
    tick = sp["tick"]
    if variant.startswith("A"):
        kind, h = variant.split("-")
        bars = R.source_bars(sym, 15)
        ctx = WF.Ctx(bars, sym, 15)
        ev = A.signals(bars, data["summ"][int(h[:-1])], ctx.atr, tick, kind, level_seed=seed)
        limit = kind == "A1"
        tf = 15
    else:
        tf = 15 if variant == "B15" else 60
        bars = R.source_bars(sym, tf)
        ctx = WF.Ctx(bars, sym, tf)
        tdays = [BL.tday(dt.datetime.fromisoformat(b["ts"])) for b in bars]
        ev = Bm.signals(bars, tdays, Bm.day_level_map(data["prof60"], level_seed=seed), tick)
        limit = False
    res = run_ext(bars, sp, ev, limit, ctx.atr, make_stack_fn(sym, bars, tf, data["prof60"], ctx))
    res["n_signals"] = len(ev)
    res["first_ts"], res["last_ts"] = bars[0]["ts"], bars[-1]["ts"]
    return res


VARIANTS = ["A1-24h", "A1-48h", "A1-72h", "A2-24h", "A2-48h", "A2-72h", "B15", "B60"]
SUBSETS = {"all": lambda t: True, "stacked": lambda t: t["stacked"], "not stacked": lambda t: not t["stacked"]}


def cell(trades, plc_runs):
    sc = WF.score({"trades": trades}) if trades else {"real": {"n": 0}}
    d = sc["real"]
    lm = [sum(t["r"] for t in ts) / len(ts) for ts in plc_runs if ts]
    beats = sum(m < (d.get("mean_r") or 0) for m in lm) if trades else 0
    row = {"n": d.get("n", 0), "win": d.get("win_rate"), "payoff": d.get("payoff"), "avg_r": d.get("mean_r"),
           "t": d.get("t"), "p1": sc.get("placebo_P1", {}).get("mean_r"), "z": sc.get("z_vs_placebo"),
           "lvl_avg": round(sum(lm) / len(lm), 4) if lm else None, "lvl_n": round(sum(len(ts) for ts in plc_runs) / max(1, len(plc_runs)), 1),
           "beats": f"{beats}/{len(lm)}", "h1": d.get("first_half"), "h2": d.get("second_half")}
    row["pass"] = bool(row["n"] >= 30 and (row["t"] or 0) >= LUCK and (row["z"] or 0) >= LUCK and beats >= 9)
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {s: symbol_data(s) for s in SYMBOLS}
    real, plc, meta = {}, {}, {}
    for v in VARIANTS:
        for s in SYMBOLS:
            r = run_variant(s, v, data[s])
            real[(v, s)] = r["trades"]
            meta[(v, s)] = {"signals": r["n_signals"], "refused": len(r["refused"]), "skipped": len(r["skipped"]),
                            "equity": r["equity"], "span": f"{r['first_ts'][:10]}..{r['last_ts'][:10]}"}
            plc[(v, s)] = [run_variant(s, v, data[s], seed=k)["trades"] for k in range(LEVEL_SEEDS)]
            (OUT / f"trades_{v}_{s}.jsonl").write_text("".join(json.dumps(t) + "\n" for t in r["trades"]))
            print(f"{v} {s}: signals {r['n_signals']} trades {len(r['trades'])} refused {len(r['refused'])} "
                  f"skipped {len(r['skipped'])}", flush=True)
    rows = []
    for v in VARIANTS:
        for s in list(SYMBOLS) + ["POOLED"]:
            syms = SYMBOLS if s == "POOLED" else (s,)
            for sub, f in SUBSETS.items():
                tr = [t for x in syms for t in real[(v, x)] if f(t)]
                if s == "POOLED":
                    tr.sort(key=lambda t: t["entry_ts"])
                pr = [[t for x in syms for t in plc[(v, x)][k] if f(t)] for k in range(LEVEL_SEEDS)]
                rows.append({"variant": v, "symbol": s, "subset": sub, **cell(tr, pr)})
    out = {"luck_bar": LUCK, "n_tried": N_TRIED, "rows": rows,
           "meta": {f"{v}|{s}": m for (v, s), m in meta.items()},
           "rule_sha": {"A": WF.file_sha(A_PATH), "B": WF.file_sha(B_PATH)}}
    (OUT / "results.json").write_text(json.dumps(out, indent=1, default=str))
    hdr = ("| variant | symbol | subset | N | win % | payoff | avg R | t | P1 placebo avg R | z vs P1 | "
           "level-placebo avg R (avg N) | real beats level placebo | 1st / 2nd half avg R | passes |")
    lines = [hdr, "|" + "---|" * 14]
    fm = lambda x: "—" if x is None else x
    for r in rows:
        lines.append(f"| {r['variant']} | {r['symbol']} | {r['subset']} | {r['n']} | "
                     f"{fm(None if r['win'] is None else round(100 * r['win'], 1))} | {fm(r['payoff'])} | {fm(r['avg_r'])} | "
                     f"{fm(r['t'])} | {fm(r['p1'])} | {fm(r['z'])} | {fm(r['lvl_avg'])} ({r['lvl_n']}) | {r['beats']} | "
                     f"{fm(r['h1'])} / {fm(r['h2'])} | {'YES' if r['pass'] else 'no'} |")
    lines += ["", f"Luck bar sqrt(2 ln {N_TRIED}) = {LUCK}. Rule sha A {out['rule_sha']['A']}, B {out['rule_sha']['B']}.", "",
              "| variant | symbol | signals | refused (size) | skipped (late/roll/beyond stop) | end equity | data span |",
              "|---|---|---|---|---|---|---|"]
    for (v, s), m in meta.items():
        lines.append(f"| {v} | {s} | {m['signals']} | {m['refused']} | {m['skipped']} | {m['equity']} | {m['span']} |")
    (OUT / "tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("PASSING CELLS:", [(r["variant"], r["symbol"], r["subset"]) for r in rows if r["pass"]])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Deterministic walk-forward engine: replay a PRE-REGISTERED rule bar by bar, with placebos.

It does what the LLM replay desk does, but in seconds and with the rule written down in advance.
Fills, stops, sizing, costs and the 16:00 flat come from the harness the REPLAY desk uses
(`workspace/roundtable/lib/replay.py`). The pure functions are imported, and the rest is
reimplemented step for step (see DATA_HUB/sources/automation_audit_REPLAY.md §3):

  * an order decided after bar i fills at the OPEN of bar i+1, one tick worse;
  * sizing is the drawdown ladder (`replay._size`). Under min_dollar_risk the account is
    ABSORBED and the run stops;
  * each bar resolves the stop first (the stop wins a same-bar tie). A gap through the stop exits
    at the open, a gap through the target at the open in your favour;
  * nothing is held 16:00-18:00 ET, and a position is closed at the first 16:00 after entry;
  * cost = the contract's round turn per contract, and R = net / dollars at risk.

Controls (the harness placebo reused absolute stop/target prices, finding F1; this one does not):
  P1  direction placebo: same bar, same stop/target DISTANCES from its own fill, random side,
      K draws. It answers "does choosing the direction beat a coin flip through the same exits?"
  P3  level placebo (only for rules that use ctx.levels): the whole run repeated with the rule's
      levels replaced by random prices in the same range. It answers "is it the level, or just
      the approach?"

A rule is a Python file exporting NAME, PREREG (dict with 'family' and 'text'), WARMUP, optional
observe(view, i, ctx) (called on EVERY bar, e.g. to arm levels), and
decide(view, i, ctx) -> dict | None (called only when flat), where the dict is
    {"side": "LONG"|"SHORT", "stop": px | None, "target": px | None,
     "stop_atr": k, "target_atr": k, "target_r": k, "why": str}
Relative stops and targets are resolved against the actual fill.

The luck bar comes from DATA_HUB/walkforward/LEDGER.tsv. A rule must be registered there
(--register) before it can run, so the number of ideas tried is counted by the tool, not
declared by whoever ran it.

    python3 DATA_HUB/tools/walkforward.py --rule DATA_HUB/tools/rules/lvn_fade_1w60.py --register
    python3 DATA_HUB/tools/walkforward.py --rule DATA_HUB/tools/rules/lvn_fade_1w60.py --symbol MES --tf 60
    python3 DATA_HUB/tools/walkforward.py --regression      # must reproduce REPLAY R1's two trades
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "workspace" / "roundtable" / "lib"))
sys.path.insert(0, str(ROOT / "DATA_HUB" / "tools"))
import replay as R  # noqa: E402  (pure helpers; importing only reads desk-config.json)

OUT = ROOT / "DATA_HUB" / "walkforward"
LEDGER = OUT / "LEDGER.tsv"
LEAK_Z = 4.5


# ------------------------------------------------------------------ causal context
class View:
    """Read-only window on bars[:i+1]. Touching the future raises, so a rule cannot peek."""

    def __init__(self, bars, i):
        self._b, self._i = bars, i

    def __getitem__(self, k):
        if isinstance(k, slice):
            stop = k.stop if k.stop is not None else self._i + 1
            if stop > self._i + 1:
                raise IndexError("look-ahead: slice past the current bar")
            return self._b[k.start or 0:stop:k.step]
        if k > self._i or k < 0:
            raise IndexError(f"look-ahead: bar {k} requested at bar {self._i}")
        return self._b[k]

    def __len__(self):
        return self._i + 1


class Ctx:
    """Causal helpers shared by rules. ATR/tday come from the hub scanners, so the rules and the
    scanners agree on definitions."""

    def __init__(self, bars, symbol, tf, level_seed=None):
        from bounce_levels import tday
        self.bars, self.symbol, self.tf = bars, symbol, tf
        self.tday = tday
        self.level_seed = level_seed           # set => ctx.levels() returns placebo prices
        self.state: dict = {}
        self._atr = self._atr_series()
        self._profiles: dict = {}
        self._parsed = None

    def _atr_series(self, n=14):
        out, trs, prev = [], [], None
        for b in self.bars:
            tr = b["h"] - b["l"] if prev is None else max(b["h"] - b["l"], abs(b["h"] - prev), abs(b["l"] - prev))
            trs.append(tr)
            prev = b["c"]
            out.append(sum(trs[-n:]) / n if len(trs) >= n else None)
        return out

    def atr(self, i):
        """ATR14 through bar i inclusive (causal)."""
        return self._atr[i] if 0 <= i < len(self._atr) else None

    def ts(self, i):
        return dt.datetime.fromisoformat(self.bars[i]["ts"])

    def profile(self, i, window_days):
        """Volume profile of the `window_days` trading days BEFORE bar i's trading day
        (vp_levels.build_profile, so identical to the scanner's). Cached per trading day."""
        from vp_levels import build_profile
        from bounce_levels import B
        d = self.tday(self.ts(i))
        key = (d, window_days)
        if key not in self._profiles:
            if self._parsed is None:
                self._parsed = [B(dt.datetime.fromisoformat(b["ts"]), b["o"], b["h"], b["l"], b["c"],
                                  float(b.get("v", 0) or 0)) for b in self.bars]
                self._days = [self.tday(b.ts) for b in self._parsed]
            idx = [k for k in range(i) if self._days[k] < d]
            days = sorted(set(self._days[k] for k in idx))[-window_days:]
            src = [self._parsed[k] for k in idx if self._days[k] in set(days)] if len(days) == window_days else []
            self._profiles[key] = build_profile(src) if src else None
        return self._profiles[key]

    def levels(self, i, kind, window_days):
        """Levels of `kind` ('lvn'|'hvn') from profile(i). In a level-placebo run, the same NUMBER
        of random prices inside the profile's range, fixed for the trading day."""
        pf = self.profile(i, window_days)
        if not pf:
            return []
        real = list(getattr(pf, kind))
        if self.level_seed is None:
            return real
        d = self.tday(self.ts(i))
        rng = random.Random(f"{self.level_seed}:{d}:{kind}:{window_days}")
        return [rng.uniform(pf.lo, pf.hi) for _ in real]


# ------------------------------------------------------------------ engine
def _round(sp, px):
    return R._round(sp, px)


def roll_masked(ts: str) -> bool:
    """Calendar roll mask, known in advance: 7 calendar days before to 1 day after each CME quarterly
    expiry (third Friday of Mar/Jun/Sep/Dec). Bars there can be two contract months glued together."""
    d = dt.datetime.fromisoformat(ts).date()
    for m in (3, 6, 9, 12):
        for y in (d.year - 1, d.year, d.year + 1):
            first = dt.date(y, m, 1)
            fri = first + dt.timedelta(days=(4 - first.weekday()) % 7 + 14)
            if fri - dt.timedelta(days=7) <= d <= fri + dt.timedelta(days=1):
                return True
    return False


def resolve_bar(pos, bar, sp):
    """One bar of exits, exactly as replay._resolve. Returns (exit_px, reason) or None."""
    sign = 1 if pos["side"] == "LONG" else -1
    stop, tgt = pos["stop"], pos.get("target")
    hit_stop = bar["l"] <= stop if sign > 0 else bar["h"] >= stop
    hit_tgt = tgt is not None and (bar["h"] >= tgt if sign > 0 else bar["l"] <= tgt)
    if hit_stop:
        gapped = bar["o"] <= stop if sign > 0 else bar["o"] >= stop
        return _round(sp, bar["o"] if gapped else stop), ("STOP_GAP" if gapped else "STOP")
    if hit_tgt:
        gapped = bar["o"] >= tgt if sign > 0 else bar["o"] <= tgt
        return _round(sp, bar["o"] if gapped else tgt), "TARGET"
    if R.in_forbidden_window(bar["ts"]) or R.cycle_deadline_crossed(pos["entry_ts"], bar["ts"]):
        return _round(sp, bar["c"]), "SESSION_FLAT"
    return None


def pnl_r(pos, px, sp):
    sign = 1 if pos["side"] == "LONG" else -1
    gross = (px - pos["entry"]) * sign * sp["point_value"] * pos["n"]
    net = gross - sp["cost_per_contract_round_turn"] * pos["n"]
    return net, net / pos["risk_dollars"]


def make_position(order, bar, sp, n=None, st=None, fill_side=None):
    """Fill at the open +/- 1 tick. Relative stops/targets are anchored to the fill."""
    side = fill_side or order["side"]
    sign = 1 if side == "LONG" else -1
    entry = _round(sp, bar["o"] + sign * sp["tick"])
    if order.get("stop") is not None and fill_side is None:
        stop = _round(sp, order["stop"])
    else:
        stop = _round(sp, entry - sign * order["_stop_dist"])
    risk_pts = abs(entry - stop)
    if order.get("target") is not None and fill_side is None:
        tgt = _round(sp, order["target"])
    elif order.get("_tgt_dist") is not None:
        tgt = _round(sp, entry + sign * order["_tgt_dist"])
    elif order.get("target_r") is not None:
        tgt = _round(sp, entry + sign * order["target_r"] * risk_pts)
    else:
        tgt = None
    note = ""
    if n is None:
        n, _, note = R._size(st, entry, stop)
        if n == 0:
            return None, note
    return {"side": side, "entry": entry, "stop": stop, "target": tgt, "n": n, "entry_ts": bar["ts"],
            "risk_dollars": risk_pts * sp["point_value"] * n, "why": order.get("why", "")}, note


def run(bars, symbol, rule, ctx, sp, *, start=0, end=None, legacy_placebo=False, roll_mask=True,
        placebo_draws=1000, seed="wf-v1", fixture=None):
    """Walk bars[start:end]. `fixture` = {i: order} replaces the rule (used by the regression test)."""
    end = len(bars) if end is None else min(end, len(bars))
    st = {"spec": sp, "equity": 50_000.0, "peak": 50_000.0}
    trades, refused, skipped, events = [], [], [], []
    pos = pending = None
    absorbed = None
    for i in range(start, end):
        bar = bars[i]
        if pending is not None:
            order, pending = pending, None
            if order.get("stop") is None:
                a = ctx.atr(i - 1) or 0
                order["_stop_dist"] = order.get("stop_atr", 1.0) * a
                if order.get("target_atr") is not None:
                    order["_tgt_dist"] = order["target_atr"] * a
            late = dt.datetime.fromisoformat(bar["ts"]).hour in (15, 16)
            if fixture is None and late:
                skipped.append({"i": i, "ts": bar["ts"], "why": "fill bar 15:xx/16:xx (no late entries, rule 5)"})
            elif fixture is None and roll_mask and roll_masked(bar["ts"]):
                skipped.append({"i": i, "ts": bar["ts"], "why": "roll mask"})
            else:
                pos, note = make_position(order, bar, sp, st=st)
                if pos is None:
                    refused.append({"i": i, "ts": bar["ts"], "why": note})
                    if note.startswith("ABSORBING"):
                        absorbed = bar["ts"]
                        break
                else:
                    pos["order"] = order
                    pos["i"] = i
        if pos is not None:
            ex = resolve_bar(pos, bar, sp)
            if ex:
                px, reason = ex
                net, r = pnl_r(pos, px, sp)
                st["equity"] += net
                st["peak"] = max(st["peak"], st["equity"])
                t = {"entry_i": pos["i"], "entry_ts": pos["entry_ts"], "exit_ts": bar["ts"], "side": pos["side"],
                     "entry": pos["entry"], "stop": pos["stop"], "target": pos["target"], "n": pos["n"],
                     "exit": px, "reason": reason, "net": round(net, 2), "r": round(r, 4),
                     "equity": round(st["equity"], 2), "why": pos["why"]}
                t["placebo"] = placebo_outcomes(bars, pos, sp, legacy=legacy_placebo)
                trades.append(t)
                pos = None
        if fixture is None and rule is not None and hasattr(rule, "observe") and i >= getattr(rule, "WARMUP", 0):
            rule.observe(View(bars, i), i, ctx)          # per-bar state (e.g. level arming), even while positioned
        if pos is None and pending is None and i + 1 < end:
            if fixture is not None:
                o = fixture.get(i)
            elif i >= getattr(rule, "WARMUP", 0):
                o = rule.decide(View(bars, i), i, ctx)
            else:
                o = None
            if o:
                pending = dict(o)
                events.append({"i": i, "ts": bar["ts"], "side": o["side"], "why": o.get("why", "")})
    return {"trades": trades, "refused": refused, "skipped": skipped, "decisions": events,
            "absorbed": absorbed, "equity": round(st["equity"], 2),
            "max_dd": round(max_drawdown([t["net"] for t in trades]), 2)}


def placebo_outcomes(bars, pos, sp, legacy=False):
    """R of the same trade taken LONG and SHORT from the same bar with the same distances
    (P1). Each placebo draw just picks one side, so both are simulated once. legacy=True
    reproduces the harness's absolute-price placebo (finding F1) for the parity test only."""
    out = {}
    i0 = pos["i"]
    for side in ("LONG", "SHORT"):
        sign = 1 if side == "LONG" else -1
        entry = _round(sp, bars[i0]["o"] + sign * sp["tick"])
        if legacy:
            stop, tgt = pos["order"].get("stop", pos["stop"]), pos["order"].get("target", pos["target"])
        else:
            d_stop = abs(pos["entry"] - pos["stop"])
            d_tgt = abs(pos["target"] - pos["entry"]) if pos["target"] is not None else None
            stop = _round(sp, entry - sign * d_stop)
            tgt = _round(sp, entry + sign * d_tgt) if d_tgt is not None else None
        p = {"side": side, "entry": entry, "stop": stop, "target": tgt, "n": pos["n"], "entry_ts": pos["entry_ts"]}
        p["risk_dollars"] = abs(entry - stop) * sp["point_value"] * pos["n"] or 1e-9
        r = None
        for j in range(i0, len(bars)):
            ex = resolve_bar(p, bars[j], sp)
            if ex:
                r = round(pnl_r(p, ex[0], sp)[1], 4)
                break
        out[side] = r if r is not None else 0.0
    return out


# ------------------------------------------------------------------ statistics
def max_drawdown(nets):
    eq = peak = dd = 0.0
    for x in nets:
        eq += x
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    return dd


def describe(rs):
    n = len(rs)
    if not n:
        return {"n": 0}
    m = sum(rs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in rs) / (n - 1)) if n > 1 else 0.0
    wins = [x for x in rs if x > 0]
    losses = [x for x in rs if x <= 0]
    payoff = (sum(wins) / len(wins)) / abs(sum(losses) / len(losses)) if wins and losses and sum(losses) else None
    return {"n": n, "mean_r": round(m, 4), "sd": round(sd, 4), "t": round(m / (sd / math.sqrt(n)), 3) if sd else None,
            "win_rate": round(len(wins) / n, 3), "payoff": round(payoff, 3) if payoff else None,
            "first_half": round(sum(rs[: n // 2]) / max(1, n // 2), 4),
            "second_half": round(sum(rs[n // 2:]) / max(1, n - n // 2), 4)}


def score(res, draws=1000, seed="wf-v1"):
    real = [t["r"] for t in res["trades"]]
    d = describe(real)
    if not real:
        return {"real": d}
    rng = random.Random(seed)
    means, pooled = [], []
    for _ in range(draws):
        rs = [t["placebo"][rng.choice(("LONG", "SHORT"))] for t in res["trades"]]
        means.append(sum(rs) / len(rs))
        pooled += rs
    p = describe(pooled)
    se = math.sqrt((d["sd"] ** 2) / d["n"] + (p["sd"] ** 2) / p["n"]) if d["n"] > 1 else 0
    z = (d["mean_r"] - p["mean_r"]) / se if se else None
    emp_p = (1 + sum(m >= d["mean_r"] for m in means)) / (draws + 1)
    return {"real": d, "placebo_P1": {"mean_r": p["mean_r"], "sd": p["sd"], "draws": draws},
            "z_vs_placebo": round(z, 3) if z is not None else None, "empirical_p": round(emp_p, 4)}


# ------------------------------------------------------------------ ledger / rules
def load_rule(path):
    spec = importlib.util.spec_from_file_location("rule", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def file_sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:12]


def ledger_rows():
    if not LEDGER.exists():
        return []
    rows = [l.split("\t") for l in LEDGER.read_text().splitlines()[1:] if l.strip()]
    return [dict(zip(("date", "rule", "sha", "family", "trials", "text"), r)) for r in rows]


def register(rule, path):
    OUT.mkdir(parents=True, exist_ok=True)
    if not LEDGER.exists():
        LEDGER.write_text("date\trule\tsha\tfamily\ttrials\ttext\n")
    sha = file_sha(path)
    if any(r["sha"] == sha for r in ledger_rows()):
        print(f"already registered: {rule.NAME} {sha}")
        return
    pre = rule.PREREG
    with LEDGER.open("a") as fh:
        fh.write(f"{dt.date.today()}\t{rule.NAME}\t{sha}\t{pre['family']}\t{pre.get('trials', 1)}\t"
                 f"{pre['text'].replace(chr(9), ' ')}\n")
    print(f"registered {rule.NAME} sha {sha} family {pre['family']}")


def luck_bar(family):
    n = sum(int(r["trials"]) for r in ledger_rows() if r["family"] == family)
    return max(1, n), round(math.sqrt(2 * math.log(max(2, n))), 3)


# ------------------------------------------------------------------ driver
def verdict(sc, bar):
    z, t = sc.get("z_vs_placebo"), sc["real"].get("t")
    if sc["real"].get("n", 0) < 30:
        return "TOO FEW TRADES (<30): no conclusion"
    if z is not None and abs(z) > LEAK_Z:
        return f"LEAK ALARM: |z| {z} > {LEAK_Z}. Nothing in ~3M tests here beat t 3.92; audit for look-ahead"
    if (t or 0) >= bar and (z or 0) >= bar:
        return f"PASSES its luck bar {bar} (t {t}, z vs placebo {z}). Confirm out-of-sample before any money"
    if (sc["real"]["mean_r"] or 0) > 0 and (z or 0) > 0:
        return f"positive but under the luck bar {bar} (t {t}, z {z}): not an edge"
    return f"FAILS (t {t}, z vs placebo {z}, luck bar {bar})"


def to_md(rule, symbol, tf, res, sc, lvl, bar_n, bar, data_sha, nbars):
    d = sc["real"]
    lines = [f"# Walk-forward: {rule.NAME} on {symbol} {tf}m\n",
             f"_Generated by `DATA_HUB/tools/walkforward.py`. Data: {nbars} bars, sha {data_sha}._\n",
             f"**Hypothesis (pre-registered):** {rule.PREREG['text']}\n",
             f"**Verdict:** {verdict(sc, bar)}\n",
             "| measure | value |", "|---|---|",
             f"| trades | {d.get('n', 0)} |",
             f"| win rate / payoff | {d.get('win_rate')} / {d.get('payoff')} |",
             f"| average R per trade (after costs) | {d.get('mean_r')} |",
             f"| t-stat | {d.get('t')} |",
             f"| direction placebo average R | {sc.get('placebo_P1', {}).get('mean_r')} |",
             f"| z vs placebo / empirical p | {sc.get('z_vs_placebo')} / {sc.get('empirical_p')} |",
             f"| first half / second half avg R | {d.get('first_half')} / {d.get('second_half')} |",
             f"| account end equity / max drawdown | ${res['equity']:,.2f} / ${res['max_dd']:,.2f} |",
             f"| absorbed | {res['absorbed'] or 'no'} |",
             f"| refused / skipped (late or roll) | {len(res['refused'])} / {len(res['skipped'])} |",
             f"| luck bar (family {rule.PREREG['family']}, {bar_n} trials in ledger) | {bar} |"]
    if lvl:
        lines += ["", "**Level placebo** (same rule, its levels swapped for random prices in the same range):", "",
                  "| | trades | avg R |", "|---|---|---|", f"| real levels | {d.get('n')} | {d.get('mean_r')} |"]
        lines += [f"| random levels (seed {k}) | {v['n']} | {v.get('mean_r')} |" for k, v in lvl["runs"].items()]
        lines += [f"| random levels, mean of {len(lvl['runs'])} runs | — | {lvl['mean']} |",
                  f"| real beats random in | {lvl['beats']}/{len(lvl['runs'])} runs | |"]
    return "\n".join(lines) + "\n"


def cmd_run(a):
    rule = load_rule(a.rule)
    sha = file_sha(a.rule)
    if not any(r["sha"] == sha for r in ledger_rows()):
        sys.exit(f"{a.rule} (sha {sha}) is not in {LEDGER}. Register it first with --register. "
                 "Editing a rule changes its sha, so every edit counts as a new trial.")
    sp = R.spec(a.symbol)
    bars = R.source_bars(a.symbol, a.tf)
    data_sha = hashlib.sha256(json.dumps(bars).encode()).hexdigest()[:12]
    res = run(bars, a.symbol, rule, Ctx(bars, a.symbol, a.tf), sp, roll_mask=a.roll_mask != "none")
    sc = score(res, a.placebo_draws)
    lvl = None
    if getattr(rule, "USES_LEVELS", False) and a.level_placebos:
        runs = {}
        for s in range(a.level_placebos):
            r2 = run(bars, a.symbol, rule, Ctx(bars, a.symbol, a.tf, level_seed=s), sp, roll_mask=a.roll_mask != "none")
            runs[s] = describe([t["r"] for t in r2["trades"]])
        means = [v["mean_r"] for v in runs.values() if v.get("n")]
        lvl = {"runs": runs, "mean": round(sum(means) / len(means), 4) if means else None,
               "beats": sum(m < (sc["real"].get("mean_r") or 0) for m in means)}
    bar_n, bar = luck_bar(rule.PREREG["family"])
    out = OUT / f"{rule.NAME}_{a.symbol}_{a.tf}m"
    out.mkdir(parents=True, exist_ok=True)
    (out / "trades.jsonl").write_text("".join(json.dumps(t) + "\n" for t in res["trades"]))
    summary = {"rule": rule.NAME, "rule_sha": sha, "symbol": a.symbol, "tf": a.tf, "bars": len(bars),
               "data_sha": data_sha, "score": sc, "level_placebo": lvl, "luck_bar": bar, "family_trials": bar_n,
               "verdict": verdict(sc, bar), **{k: res[k] for k in ("equity", "max_dd", "absorbed")},
               "refused": len(res["refused"]), "skipped": len(res["skipped"])}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    (out / "summary.md").write_text(to_md(rule, a.symbol, a.tf, res, sc, lvl, bar_n, bar, data_sha, len(bars)))
    d = sc["real"]
    print(f"{rule.NAME} {a.symbol} {a.tf}m: n={d.get('n', 0)} win={d.get('win_rate')} payoff={d.get('payoff')} "
          f"avgR={d.get('mean_r')} t={d.get('t')} | placebo {sc.get('placebo_P1', {}).get('mean_r')} "
          f"z={sc.get('z_vs_placebo')} p={sc.get('empirical_p')}"
          + (f" | level-placebo mean {lvl['mean']} (real beats {lvl['beats']}/{len(lvl['runs'])})" if lvl else "")
          + f" | luck bar {bar} -> {summary['verdict']}")


def cmd_regression():
    """REPLAY R1 journal: ORDER at cursor 453 SHORT stop 5804 target 5768, and at cursor 1340 SHORT stop 5985.5
    target 5950 (an order at cursor c fills at bars[c]'s open, so it is decided at i = c-1). The harness
    produced +1.8949R and +1.8540R, and its legacy placebos -0.0671R and +1.8540R."""
    sp = R.spec("MES")
    bars = R.source_bars("MES", 60)
    fx = {452: {"side": "SHORT", "stop": 5804.0, "target": 5768.0},
          1339: {"side": "SHORT", "stop": 5985.5, "target": 5950.0}}
    res = run(bars, "MES", None, Ctx(bars, "MES", 60), sp, start=0, end=1500, legacy_placebo=True, fixture=fx)
    got = [(t["r"], t["reason"], t["placebo"]) for t in res["trades"]]
    exp_r = [1.8949, 1.8540]
    ok = len(got) == 2 and all(abs(g[0] - e) < 5e-4 and g[1] == "TARGET" for g, e in zip(got, exp_r))
    leg = sorted(p for g in got for p in g[2].values())
    ok_p = any(abs(x + 0.0671) < 5e-4 for x in leg) and any(abs(x - 1.854) < 5e-4 for x in leg)
    for g in got:
        print(f"  trade r={g[0]} {g[1]}  legacy-placebo LONG={g[2]['LONG']} SHORT={g[2]['SHORT']}")
    print("REGRESSION", "PASS" if ok and ok_p else "FAIL", "- engine reproduces REPLAY R1's two harness trades"
          + (" and legacy placebos" if ok_p else ""))
    sys.exit(0 if ok and ok_p else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rule")
    ap.add_argument("--symbol", default="MES")
    ap.add_argument("--tf", type=int, default=60)
    ap.add_argument("--register", action="store_true", help="add the rule to the ledger (counts as a trial)")
    ap.add_argument("--placebo-draws", type=int, default=1000)
    ap.add_argument("--level-placebos", type=int, default=10)
    ap.add_argument("--roll-mask", choices=("calendar", "none"), default="calendar")
    ap.add_argument("--regression", action="store_true")
    a = ap.parse_args()
    if a.regression:
        cmd_regression()
    if not a.rule:
        ap.error("--rule is required")
    if a.register:
        register(load_rule(a.rule), a.rule)
        return
    cmd_run(a)


if __name__ == "__main__":
    main()

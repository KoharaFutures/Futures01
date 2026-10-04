#!/usr/bin/env python3
"""LTA CONCEPT CALLOUTS — macro layer: valuation, correlation gate, seasonality, COT input.

The book builds the bias top-down: COT/sentiment -> seasonality -> valuation -> technicals
(LTA_Concepts/CONCEPTS_DIGEST.md §2). The book's indicators are proprietary; this file computes the
public stand-ins it describes, from Yahoo daily bars fetched THIS run:

  valuation  (Stealth Valuation Index proxy, book ch.20)
             diff = %chg(asset, N) - %chg(reference, N); scaled to -100..+100 by its min/max
             over the last W readings. Book settings: gold vs DXY N=10 daily W=50; indices vs
             30-yr bonds (ZB) N=13 weekly W=50; crude vs DXY N=10 daily W=50.
  corr gate  Pearson correlation of daily returns over 100 days. The book says "near 0 = do not
             use valuation" but gives no cut-off; this desk pre-registers |r| >= 0.30.
  seasonal   (FutureScope proxy, book ch.17-18) average return over the next 20 trading days
             from today's calendar date, per year, over the last 5 and 10 years, with how many
             years were positive - plus the book's stated window for the asset.
  COT        cftc.gov is blocked by this environment's network policy. Sentiment is read from
             cot_inputs.json, which the owner (or a session with access) fills by hand from the
             CFTC report or the LTA indicators. Missing = UNKNOWN, never assumed.

Extreme valuation threshold: the book gives none. Pre-registered here: |valuation| >= 80.

    python3 workspace/paper/LTA/macro.py            # MNQ MES MGC MCL
    python3 workspace/paper/LTA/macro.py --json

Every number is context for a discretionary read. None of it has been measured against a placebo
in this repo yet (see CHARTER.md §5 for the pre-registered tests).
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
from datetime import date, datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
COT_FILE = HERE / "cot_inputs.json"

# symbol -> (Yahoo continuous future, reference, reference ticker, N, interval, W, book season)
CFG = {
    "MGC": ("GC=F", "DXY", "DX-Y.NYB", 10, "1d", 50,
            "bullish Sep-Feb (Q4 & Q1), soft Q2-Q3 [pdf p124-p128]"),
    "MCL": ("CL=F", "DXY", "DX-Y.NYB", 10, "1d", 50,
            "bullish May-Jun (driving season), weak Oct-Dec [pdf p134-p135]"),
    "MNQ": ("NQ=F", "30Y bond", "ZB=F", 13, "1wk", 50,
            "bullish Apr-Jul and Oct-Jan, weak Aug-Sep [pdf p131-p132]"),
    "MES": ("ES=F", "30Y bond", "ZB=F", 13, "1wk", 50,
            "no ES window in the book; Alerts library: May-Aug firm, Aug-Oct weak [pdf p265-p266]"),
}
CORR_MIN = 0.30
VAL_EXTREME = 80.0


def _closes(ticker, interval, period):
    import yfinance as yf
    d = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
    if d is None or d.empty:
        return []
    c = d["Close"]
    if hasattr(c, "columns"):          # yfinance returns a 1-column frame for one ticker
        c = c.iloc[:, 0]
    return [(ix.date() if hasattr(ix, "date") else ix, float(v)) for ix, v in c.dropna().items()]


def _align(a, b):
    db = dict(b)
    return [(d, x, db[d]) for d, x in a if d in db]


def valuation(sym):
    tk, rname, rtk, n, iv, w, _ = CFG[sym]
    a = _closes(tk, iv, "5y")
    r = _closes(rtk, iv, "5y")
    rows = _align(a, r)
    if len(rows) < n + w + 1:
        return {"error": f"not enough aligned {iv} bars ({len(rows)})"}
    diffs = []
    for i in range(n, len(rows)):
        pa = rows[i][1] / rows[i - n][1] - 1
        pr = rows[i][2] / rows[i - n][2] - 1
        diffs.append((rows[i][0], pa - pr))
    win = [x for _d, x in diffs[-w:]]
    lo, hi = min(win), max(win)
    now = diffs[-1][1]
    val = 0.0 if hi == lo else 200 * (now - lo) / (hi - lo) - 100
    tag = ("UNDERVALUED vs " + rname) if val <= -VAL_EXTREME else \
          ("OVERVALUED vs " + rname) if val >= VAL_EXTREME else "neutral"
    return {"asset": tk, "reference": f"{rname} ({rtk})", "N": n, "interval": iv, "W": w,
            "value": round(val, 1), "reading": tag, "source_bar": str(diffs[-1][0])}


def corr_gate(sym, days=100):
    tk, rname, rtk, *_ = CFG[sym]
    rows = _align(_closes(tk, "1d", "1y"), _closes(rtk, "1d", "1y"))[-(days + 1):]
    if len(rows) < 30:
        return {"error": "not enough daily bars"}
    ra = [rows[i][1] / rows[i - 1][1] - 1 for i in range(1, len(rows))]
    rb = [rows[i][2] / rows[i - 1][2] - 1 for i in range(1, len(rows))]
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    r = cov / (va * vb) if va and vb else 0.0
    return {"pair": f"{tk} vs {rtk}", "days": len(ra), "r": round(r, 2),
            "usable": abs(r) >= CORR_MIN, "rule": f"|r| >= {CORR_MIN} (pre-registered; book gives no cut-off)",
            "source_bar": str(rows[-1][0])}


def seasonal(sym, horizon=20):
    tk, *_rest, book = CFG[sym]
    px = _closes(tk, "1d", "max")
    if len(px) < 300:
        return {"error": "not enough daily history", "book_window": book}
    today = px[-1][0]
    out = {"book_window": book, "horizon_days": horizon, "source_bar": str(today),
           "caveat": "continuous Yahoo future: roll gaps included (gold daily rolls are large, see SERIES_AUDIT)"}
    for yrs in (5, 10):
        rets = []
        for y in range(today.year - yrs, today.year):
            try:
                anchor = date(y, today.month, min(today.day, 28))
            except ValueError:
                continue
            i = next((k for k, (d, _c) in enumerate(px) if d >= anchor), None)
            if i is None or i + horizon >= len(px):
                continue
            rets.append(px[i + horizon][1] / px[i][1] - 1)
        if rets:
            out[f"{yrs}y"] = {"years": len(rets), "avg_pct": round(100 * sum(rets) / len(rets), 2),
                              "positive": sum(1 for x in rets if x > 0)}
    return out


def macro_trend(sym):
    """Pre-registered stand-in for the book's 'macro trend' (it reads it off weekly/monthly
    structure by eye): UP if the daily close is above its 100-day average and that average is
    higher than 20 days ago; DOWN for the mirror; otherwise RANGE."""
    px = [c for _d, c in _closes(CFG[sym][0], "1d", "2y")]
    if len(px) < 130:
        return {"error": "not enough daily bars"}
    sma = lambda k: sum(px[len(px) - k - 100:len(px) - k]) / 100
    now, then = sma(0), sma(20)
    t = "UP" if px[-1] > now and now > then else "DOWN" if px[-1] < now and now < then else "RANGE"
    return {"trend": t, "close": round(px[-1], 4), "sma100": round(now, 4), "sma100_20d_ago": round(then, 4),
            "rule": "close vs SMA100(daily) and SMA100 slope over 20 days"}


def cot(sym):
    if not COT_FILE.exists():
        return {"status": "UNKNOWN", "why": "cot_inputs.json missing; cftc.gov is blocked here"}
    d = json.loads(COT_FILE.read_text()).get(sym)
    if not d:
        return {"status": "UNKNOWN", "why": f"no {sym} entry in cot_inputs.json"}
    return d


def bias_summary(m):
    """Count the book's macro layers that point one way. The book: one or two strong ones can be
    enough, two or three aligned = conviction [pdf p174]. Seasonality counts only as an
    'additional confluence', valuation only with a usable correlation."""
    up = dn = 0
    notes = []
    v, g = m.get("valuation", {}), m.get("corr_gate", {})
    tr = m.get("macro_trend", {}).get("trend")
    # book (pdf p260-p261): valuation counts WITH the macro trend; counter-trend needs extra proof
    if g.get("usable") and "UNDER" in v.get("reading", ""):
        if tr == "UP":
            up += 1; notes.append("valuation: undervalued inside a macro uptrend (book: continuation)")
        else:
            notes.append(f"valuation: undervalued but macro trend {tr} — counter-trend, not counted")
    if g.get("usable") and "OVER" in v.get("reading", ""):
        if tr == "DOWN":
            dn += 1; notes.append("valuation: overvalued inside a macro downtrend (book: continuation)")
        else:
            notes.append(f"valuation: overvalued but macro trend {tr} — counter-trend, not counted")
    c = m.get("cot", {})
    if c.get("bias") in ("BULLISH", "BEARISH"):
        if c["bias"] == "BULLISH":
            up += 1
        else:
            dn += 1
        notes.append(f"COT: {c['bias']} ({c.get('detail', '')}, as of {c.get('as_of', '?')})")
    s = m.get("seasonal", {}).get("10y")
    if s and s["years"] >= 8:
        if s["positive"] >= 7 and s["avg_pct"] > 0:
            up += 1; notes.append(f"seasonal: {s['positive']}/{s['years']} yrs up next {m['seasonal']['horizon_days']}d")
        elif s["positive"] <= s["years"] - 7 and s["avg_pct"] < 0:
            dn += 1; notes.append(f"seasonal: {s['years'] - s['positive']}/{s['years']} yrs down next {m['seasonal']['horizon_days']}d")
    bias = "BULLISH" if up > dn else "BEARISH" if dn > up else "NONE"
    return {"bias": bias, "layers_up": up, "layers_down": dn, "notes": notes}


def run(sym):
    m = {"symbol": sym, "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for k, f in (("macro_trend", macro_trend), ("valuation", valuation), ("corr_gate", corr_gate),
                 ("seasonal", seasonal), ("cot", cot)):
        try:
            m[k] = f(sym)
        except Exception as e:                       # a failed fetch is reported, never filled in
            m[k] = {"error": f"{type(e).__name__}: {e}"}
    m["macro_bias"] = bias_summary(m)
    return m


def to_md(m):
    v, g, s, c, b = m["valuation"], m["corr_gate"], m["seasonal"], m["cot"], m["macro_bias"]
    L = [f"### {m['symbol']} macro layer (fetched {m['fetched_utc']} UTC)", ""]
    L.append(f"- **Macro bias (layers):** {b['bias']} — up {b['layers_up']} / down {b['layers_down']}"
             + (": " + "; ".join(b["notes"]) if b["notes"] else ""))
    t = m["macro_trend"]
    L.append(f"- **Macro trend (daily):** {t.get('trend', 'error ' + t.get('error', ''))}"
             + (f" — close {t['close']} vs SMA100 {t['sma100']} (20d ago {t['sma100_20d_ago']})" if "sma100" in t else ""))
    if "error" in v:
        L.append(f"- **Valuation:** error {v['error']}")
    else:
        L.append(f"- **Valuation** vs {v['reference']} (N={v['N']} {v['interval']}, W={v['W']}): "
                 f"**{v['value']:+}** → {v['reading']} · bar {v['source_bar']}")
    if "error" in g:
        L.append(f"- **Correlation gate:** error {g['error']}")
    else:
        L.append(f"- **Correlation gate:** r = {g['r']} over {g['days']} days → "
                 f"{'usable' if g['usable'] else 'NOT usable — ignore valuation'} ({g['rule']})")
    L.append(f"- **Seasonality (book):** {s.get('book_window')}")
    for y in ("5y", "10y"):
        if y in s:
            L.append(f"  - own calc, next {s['horizon_days']} trading days, last {y}: avg {s[y]['avg_pct']:+}% , "
                     f"{s[y]['positive']}/{s[y]['years']} years up")
    if "error" in s:
        L.append(f"  - own calc: error {s['error']}")
    L.append(f"- **COT / sentiment:** {c.get('bias', c.get('status'))} — {c.get('detail', c.get('why', ''))}")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--symbols", nargs="+", default=list(CFG))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    ms = [run(s) for s in a.symbols]
    print(json.dumps(ms, indent=1, default=str) if a.json else "\n".join(to_md(m) for m in ms))


if __name__ == "__main__":
    main()

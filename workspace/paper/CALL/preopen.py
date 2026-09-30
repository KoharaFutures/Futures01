#!/usr/bin/env python3
"""Pre-open review (owner, 2026-09-29 17:53 ET): in the 10 minutes before the 18:00 ET reopen, build
24h / 48h / 72h volume profiles for MGC and MNQ from the desk's 5m bars and list POC, value area and
LVNs nearest the last price, so candidate positions can be drafted with plan_builder before the open.

    python3 workspace/paper/CALL/preopen.py            # prints a report, writes preopen/<date>.md

Method: each 5m bar's volume is spread evenly across the price bins its high-low range covers
(MNQ 5-pt bins, MGC 1-pt bins). POC = busiest bin; value area = 70% of volume grown out from the POC;
LVN = a bin whose 3-bin smoothed volume is a local minimum below 50% of the POC's, with heavier volume on
both sides. Caveat from the hub: LVNs on 5m-built 1-3 day profiles have measured as coin flips; the
60m-built 1-week+ profiles are where the bounce lean was found. This is a map, not an edge.
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import resolve  # noqa: E402

BIN = {"MNQ": 5.0, "MGC": 1.0}
WINDOWS = (24, 48, 72)


def profile(bars, step):
    vol = {}
    for b in bars:
        lo, hi, v = b["l"], b["h"], float(b.get("v") or 0)
        if v <= 0:
            continue
        k0, k1 = int(lo // step), int(hi // step)
        n = k1 - k0 + 1
        for k in range(k0, k1 + 1):
            vol[k] = vol.get(k, 0.0) + v / n
    return vol


def summarize(vol, step):
    ks = sorted(vol)
    tot = sum(vol.values())
    poc = max(vol, key=vol.get)
    lo = hi = poc
    acc = vol[poc]
    while acc < 0.7 * tot and (lo > ks[0] or hi < ks[-1]):
        dn = vol.get(lo - 1, 0.0) if lo > ks[0] else -1
        up = vol.get(hi + 1, 0.0) if hi < ks[-1] else -1
        if up >= dn:
            hi += 1; acc += max(up, 0)
        else:
            lo -= 1; acc += max(dn, 0)
    sm = {k: (vol.get(k - 1, 0) + vol.get(k, 0) + vol.get(k + 1, 0)) / 3 for k in ks}
    pv = vol[poc]
    lvns = []
    for k in ks[2:-2]:
        if sm[k] < sm[k - 1] and sm[k] <= sm[k + 1] and sm[k] < 0.5 * pv:
            left = max(sm[j] for j in ks if j < k)
            right = max(sm[j] for j in ks if j > k)
            if left > 1.5 * sm[k] and right > 1.5 * sm[k]:
                lvns.append(k)
    mid = lambda k: round((k + 0.5) * step, 2)
    # LVN DEPTH (owner lesson, MGC 4220 on 2026-09-29): the reversal zone was the DEEPEST valley between two
    # heavy shelves (4205-07 value top and the 4228-30 HVN): valley volume 0.19x the smaller flanking peak,
    # and the first LVN outside value. A shallow LVN (4210.5, 0.6x) got run through. Depth = valley volume /
    # the smaller of the highest peaks within 25 bins on each side; lower = thinner = stronger rejection lean.
    W = 25
    scored = []
    for k in lvns:
        lp = max(sm.get(j, 0) for j in range(k - W, k))
        rp = max(sm.get(j, 0) for j in range(k + 1, k + W + 1))
        depth = sm[k] / max(1e-9, min(lp, rp))
        side = "above value" if k > hi else ("below value" if k < lo else "inside value")
        scored.append({"price": mid(k), "depth": round(depth, 2), "where": side})
    outside = [x for x in scored if x["where"] != "inside value"]
    first_up = min((x for x in outside if x["where"] == "above value"), key=lambda x: x["price"], default=None)
    first_dn = max((x for x in outside if x["where"] == "below value"), key=lambda x: x["price"], default=None)
    return {"poc": mid(poc), "vah": round((hi + 1) * step, 2), "val": round(lo * step, 2),
            "lvns": [mid(k) for k in lvns], "lvn_scored": scored, "first_lvn_above": first_up,
            "first_lvn_below": first_dn, "range": (round(ks[0] * step, 2), round((ks[-1] + 1) * step, 2))}


def main():
    out = [f"# Pre-open review {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}", ""]
    for sym in ("MNQ", "MGC"):
        bars = resolve.load_bars(sym, 5)
        last = bars[-1]
        t_last = datetime.fromisoformat(last["ts"])
        out.append(f"## {sym}: last {last['c']} (5m bar {last['ts']})")
        for h in WINDOWS:
            w = [b for b in bars if datetime.fromisoformat(b["ts"]) > t_last - timedelta(hours=h)]
            s = summarize(profile(w, BIN[sym]), BIN[sym])
            near = sorted(s["lvns"], key=lambda p: abs(p - last["c"]))[:4]
            out.append(f"- **{h}h** ({len(w)} bars, range {s['range'][0]}-{s['range'][1]}): POC {s['poc']} · "
                       f"VAH {s['vah']} · VAL {s['val']} · LVNs nearest price {near}")
            deep = sorted([x for x in s["lvn_scored"] if abs(x["price"] - last["c"]) < 60 * BIN[sym]],
                          key=lambda x: x["depth"])[:3]
            out.append(f"  - deepest LVNs near price (depth = valley/flanking peak, lower = stronger): "
                       + ", ".join(f"{x['price']} d{x['depth']} {x['where']}" for x in deep)
                       + f" · first LVN above value {s['first_lvn_above']} · first below {s['first_lvn_below']}")
        out.append("")
    txt = "\n".join(out)
    d = HERE / "preopen"
    d.mkdir(exist_ok=True)
    (d / f"{datetime.now():%Y-%m-%d}.md").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()

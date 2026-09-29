"""OQ1: short the first touch from below of an LVN on the 60m-built 1-week volume profile.

Pre-registered 2026-09-29 from DATA_HUB/OPEN_QUESTIONS.md #1, before this rule was ever run. It is the
owner's method in its best-evidenced form: across all four symbols, LVNs on the 60m 1-week profile that
price RISES into continued 17 points less often than random prices in the same range
(levels/CONSISTENCY.md, n=177, 4/4 symbols).

Definitions are imported from the hub scanners, not re-tuned:
  profile  vp_levels.build_profile over the 5 trading days before today (80 bins, LVN <= 0.5 x smaller
           neighbouring HVN, HVN >= 0.25 x POC, >= 4 bins apart)
  arming   a level arms when a prior bar's HIGH is below L - 1.0 x ATR14; one trigger per arming
  trigger  bar i's high reaches L while armed-from-below
  order    SHORT at the next open; stop = fill + 1 ATR, target = fill - 1 ATR (ATR14 through bar i)
Declared difference from the scanner: the scanner measured +/-1 ATR from the LEVEL, this trades from
the FILL. No close-back-below, trend or volume filter. Adding any of those is a new ledger entry.
"""
NAME = "OQ1_lvn_fade_1w60"
WARMUP = 6 * 23
USES_LEVELS = True
PREREG = {"family": "OQ1", "trials": 4, "text": "Short the first touch from below of an LVN on the 60m-built 1-week "
          "volume profile; stop = target = 1 ATR from the fill; no other filters. Run on MES, MNQ, MGC, MCL 60m."}

WINDOW_DAYS = 5
ARM_ATR = 1.0


def observe(view, i, ctx):
    """Arm every current LVN whose price the PREVIOUS bar stayed at least 1 ATR below."""
    a = ctx.atr(i - 1)
    if not a:
        return
    d = ctx.tday(ctx.ts(i))
    armed = ctx.state.setdefault("armed", {})
    fired = ctx.state.setdefault("fired", [])
    tick = 0.01
    for L in ctx.levels(i, "lvn", WINDOW_DAYS):
        key = (d, round(L / tick))
        if view[i - 1]["h"] < L - ARM_ATR * a:
            armed[key] = True
        elif armed.get(key) and view[i]["h"] >= L:
            armed[key] = False                       # one trigger per arming, positioned or not
            fired.append((i, L))


def decide(view, i, ctx):
    fired = ctx.state.get("fired", [])
    if fired and fired[-1][0] == i:
        L = fired[-1][1]
        return {"side": "SHORT", "stop": None, "target": None, "stop_atr": 1.0, "target_atr": 1.0,
                "why": f"LVN {L:.2f} (1-week 60m profile) touched from below"}
    return None

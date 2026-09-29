#!/usr/bin/env python3
"""The scenario map: nearest key levels, and BOTH branches out of each one.

Reads ONLY visible.jsonl. This is what the account owner asked for - the thing a
chartist does when they draw a level and then sketch what happens if it holds and
what happens if it does not. It draws nothing. For the current bar it lists the
nearest detected levels above and below, and for each gives the pre-planned
geometry of FOUR branches: it holds, it breaks, neither happens, or it is GAPPED
THROUGH - resolved at a price nobody could have transacted. The fourth branch is
not decoration: SERIES_AUDIT section 3 measured open[i+1] != close[i] on 57-80% of
MES 60m boundaries, and it voided a live armed plan at bar 1616 when a 10.75-point
holiday gap cut a planned 2.00 R:R to 1.55.

READ THIS BEFORE USING IT. THE BOUNCE STUDY IS DEAD — measured, not suspected.
Every number that used to stand here (fresh extreme 45.7% bounce, n=162; retested
53.7%; random control 55.0%; "the one thing worth knowing") is WITHDRAWN. It was
compared against a control that fabricated its touch counts from choice([2,2,3,4]),
so it contained no 1-touch line at all — a 1-touch treatment against a 2+-touch
control — drew 12 lines per bar against 9.78 real ones, left a fifth of itself
sitting inside the test band of a REAL level, and tested in a 31% louder tape
(ATR 23.80 vs 18.34).

agents/E9_levels_fair.py rebuilds that control properly: count-matched to the real
level population, touch-matched by resampling the REAL touch distribution (58.0% of
real levels are 1-touch), and decontaminated — any control line landing within
0.25 ATR of a real level is redrawn, verified at 0.0% residual contamination.
Run at bar 3450:

    population                    real          fair control D    diff      z
    1-touch fresh extreme      50.1% (n=477)    54.5% (n=433)    -4.4%    -1.33
    retested, 2+ touches       55.5% (n=402)    55.2% (n=337)    +0.3%    +0.08
    bounce TRADE arm          +0.018R (n=879)   +0.076R          -0.058R    -
    break  TRADE arm          +0.015R (n=879)   +0.045R          -0.030R    -

RANDOMLY DRAWN PRICE LINES BOUNCE AS OFTEN AS THE DETECTED LEVELS, AND BOTH TRADE
ARMS PAY BETTER ON THE RANDOM LINES. The retested bucket differs from a random line
by three tenths of a percentage point. The 1-touch bucket differs in the WRONG
direction. Touch count rescues nothing: every touch-bucket claim rested on the same
fabricated control.

SO THE MAP IS NOT A FORECAST AND THE BRANCHES ARE NOT WEIGHTED. Treating the
bounce as the likely case is precisely the error the owner warned about - a level
may simply not hold, and on measurement it fails about half the time. What the map
IS for: having both branches' entry, stop, target, risk and floor-compliance
worked out BEFORE price arrives, so the decision at the bar is execution rather
than invention, and so the branch that does happen is the one that gets traded
instead of the one that was hoped for.

There is no longer any arm with a hint of separation. The BREAK arm, the last one
that had one, runs +0.015R against a fair control's +0.045R: the control wins. Both
branches of every level on this map are the branches of a coin, and the map's whole
remaining value is that it makes you write the non-bounce branch down before price
arrives.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import levels as LV

rows, N = LV.rows, LV.N
ACCOUNT_RISK, POINT_VALUE, TICK = 240.0, 5.0, 0.25
# ODDS WITHDRAWN PERMANENTLY. Withdrawn 2026-09-28 pending a fair-control rerun;
# the rerun HAPPENED (burst 18, agents/E9_levels_fair.py at bar 3450) and it did not
# rescue them — it measured the levels indistinguishable from random price lines. So
# there is nothing left to restore. The four branches stay; the probabilities do not
# come back. The owner's caution — "bounce levels may not even bounce" — is the result.
#
# These figures were published here as "measured" and they were not. Two
# independent audits killed them:
#   E7/C1 — levels.py study() line 141 hard-filters `touches < 2`, so the shipped
#     code CANNOT produce a 1-touch bucket. The 0.457/0.543 came from an ad-hoc
#     inline script, unreproducible from this repository. Worse, the random control
#     draws choice([2,2,3,4]) and so contains NO 1-touch lines at all: the one
#     "positive" result compared a 1-touch treatment against a 2+-touch control.
#   E9 — under a side-, ATR- and regime-matched control the fresh-extreme effect
#     halves and reverses in z, -8.8pp/z 1.76 -> -3.9pp/z -0.73.
#
# It steered a live decision at bar 1684, where this desk declined a trade citing
# "my own measurement says a fresh extreme BREAKS 54.3% of the time". The decline
# was right for other reasons; the number was not a measurement.
P_BOUNCE = P_BREAK = P_CTRL = P1_BOUNCE = P1_BREAK = None


def fmt_branch(name, side, entry, stop, target, a):
    risk = abs(entry - stop)
    rr = abs(target - entry) / risk if risk else 0
    floor = 0.5 * a
    ok = risk >= floor
    contracts = int(ACCOUNT_RISK // (risk * POINT_VALUE)) if risk else 0
    dollars = contracts * risk * POINT_VALUE
    flag = "" if ok else f"  <<< REFUSED: {risk:.2f}pt stop under the {floor:.2f} floor (rule 4)"
    return (f"      {name:<22} {side:<5} entry {entry:>9.2f}  stop {stop:>9.2f}  "
            f"target {target:>9.2f}  {risk:>5.2f}pt ({risk/a:.2f}ATR)  R:R {rr:.2f}  "
            f"{contracts}c ${dollars:.0f}{flag}")


def report(i=None):
    i = (N - 1) if i is None else i
    a = LV.atr(i)
    px = rows[i]["c"]
    # 1-touch levels are INCLUDED. The first version filtered them out at t>=2 and
    # so hid the most relevant level on the chart - a fresh swing high has exactly
    # one touch by definition, and it is the line a trader is actually watching.
    lv = [(L, t) for L, t in LV.levels_at(i + 1, a) if t >= 1]
    above = sorted([x for x in lv if x[0] > px], key=lambda x: x[0])[:3]
    below = sorted([x for x in lv if x[0] < px], key=lambda x: -x[0])[:3]

    print(f"SCENARIO MAP   bar {i}  {rows[i]['ts']}   close {px}   ATR14 {a:.2f} "
          f"(0.5 floor {a/2:.2f})")
    print("branch odds: WITHDRAWN. The published rates were measured against a control")
    print("with fabricated touch counts, 31% higher ATR, and zero 1-touch lines. The")
    print("branches were never weighted and now are not even nominally weighted.")
    print("=> Plan both branches. Do not bet the direction.\n")

    for tag, group in (("RESISTANCE ABOVE", above), ("SUPPORT BELOW", below)):
        print(f"  {tag}")
        if not group:
            print("      none detected within the lookback\n")
            continue
        for L, t in group:
            d = abs(L - px)
            odds = ("odds WITHDRAWN - the published bounce/break rates were measured "
                    "against an invalid control (see header). Treat BOTH branches as "
                    "unweighted; plan them, do not bet the direction.")
            print(f"    level {L:.2f}   {t} distinct touch(es)   {d:+.2f}pt away "
                  f"({d/a:.2f} ATR)")
            print(f"      odds  {odds}")
            if tag.startswith("RESISTANCE"):
                # price arrives from below: bounce = reject down, break = continue up
                print(fmt_branch("if it HOLDS (bounce)", "SHORT", L, L + a, L - 2 * a, a))
                print(fmt_branch("if it FAILS (break)", "LONG", L + 0.40 * a,
                                 L - 0.40 * a, L + 0.40 * a + 2 * (0.80 * a), a))
            else:
                print(fmt_branch("if it HOLDS (bounce)", "LONG", L, L - a, L + 2 * a, a))
                print(fmt_branch("if it FAILS (break)", "SHORT", L - 0.40 * a,
                                 L + 0.40 * a, L - 0.40 * a - 2 * (0.80 * a), a))
            print(f"      if NEITHER             price sits inside the "
                  f"{2*LV.BAND_ATR*a:.2f}pt band for {LV.HORIZON} bars -> no trade, "
                  f"level stays armed")
            print(f"      if GAPPED THROUGH      the open jumps the level -> the plan above is"
                  f" VOID, not late.")
            print(f"                             Re-check R:R at the actual fill; below 1.5,"
                  f" re-arm from the new")
            print(f"                             structure rather than chase. Observed live at"
                  f" bar 1616: a 10.75pt")
            print(f"                             holiday gap cut a planned 2.00 R:R to 1.55 and"
                  f" voided the trade.")
            print()


if __name__ == "__main__":
    report(int(sys.argv[1]) if len(sys.argv) > 1 else None)

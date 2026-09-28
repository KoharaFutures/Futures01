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

READ THIS BEFORE USING IT. levels.py measured what actually happens when price
reaches these levels, against a control of RANDOM price lines tested identically:

    fresh swing extreme     n=162   bounce 45.7%   break 54.3%   <- 1 touch
    retested level (2+)     n=175   bounce 53.7%   break 46.3%
    random price lines      n=200   bounce 55.0%   break 45.0%   <- the control

THE ONE THING WORTH KNOWING: a FRESH swing extreme - the untested high or low a
trader actually watches - BREAKS more often than it holds (54.3%), and it is the
largest deviation from the random control anywhere in the study, about 9 points
below it. Retested levels sit on top of the control and carry nothing.

Do not bank on it. On the rate that difference is z ~ 1.76, which clears the
codebase's single-pre-registered-hypothesis floor of 1.177 but NOT the ~2.33 that
this study's real search width demands - I tested touch buckets, support vs
resistance, trend alignment and 1-touch separately, so the honest n of trials is
a dozen or more, not one. And it converts to nothing in money: the bounce and
break trade arms return +0.048R and +0.045R at z +0.08 and +1.17 against random.
Rule 3 yet again - the rate moved and the expectancy did not.

The detected levels are, if anything, marginally WORSE than random at predicting
which branch happens. Touch count does not rescue it (2/3/4/5/6+ touches run
48.6 / 52.9 / 63.6 / 70.0 / 54.3% against a control that runs 53.6 / 54.7 / 60.0,
and the 6+ collapse kills the monotonic story), nor does support-vs-resistance,
nor trend alignment.

SO THE MAP IS NOT A FORECAST AND THE BRANCHES ARE NOT WEIGHTED. Treating the
bounce as the likely case is precisely the error the owner warned about - a level
may simply not hold, and on measurement it fails about half the time. What the map
IS for: having both branches' entry, stop, target, risk and floor-compliance
worked out BEFORE price arrives, so the decision at the bar is execution rather
than invention, and so the branch that does happen is the one that gets traded
instead of the one that was hoped for.

The one arm with any hint of separation is trading the BREAK (+0.063R detected
against -0.127R random, z +1.13) - not significant, and stated here only so it is
not quietly dropped.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import levels as LV

rows, N = LV.rows, LV.N
ACCOUNT_RISK, POINT_VALUE, TICK = 240.0, 5.0, 0.25
# ODDS WITHDRAWN 2026-09-28 — do not restore without a rerun against a fair control.
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

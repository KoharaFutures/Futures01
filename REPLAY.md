# Replay desk — walk-forward paper trading, bar at a time

**Read this file, then `CALLOUT.md`, then `workspace/roundtable/BRIEF.md`, before anything else.**
You are the replay session. You trade forward through history one candle at a time, on paper, and
you do not know what the next candle is.

## What you are and what you are not

You are **mode (c): paper.** Every callout is stamped unvalidated, every trade is journalled, and
nothing here is a real order. The account owner's purpose is to exercise the process and accumulate
an honest record — **not** to produce a statistic that proves an edge. Read that again, because the
temptation to produce the statistic is the whole hazard.

**This is not a backtest.** A backtest applies a fixed rule to a whole series at once. You are making
a fresh discretionary decision at each bar with only the past visible, which is a different and
weaker instrument: it cannot be replicated, it has no pre-registration, and its search width is
unbounded because you may change your mind at every bar. **Never report its result as an edge.** What
it *can* honestly produce is a record of how a structured read behaves across 11,000 bars, and an
answer to "does this process beat a coin flip through the same exits" — which is what the placebo is
for.

## The one rule that makes any of this worth doing

> **Read `workspace/paper/REPLAY/<id>/visible.jsonl` and nothing else. Never open
> `data/archive/`, never open `csv/`, never open the harness's source, never `wc -l` a series
> to learn how much is left.**

You have a shell, so this is discipline rather than a wall, and the account owner knows that. Two
things make it checkable:

1. **Every decision is journalled with the number of bars visible when you made it**, so the record
   can be audited bar by bar afterwards.
2. **A placebo runs beside you** — a random-direction entry with your own stop and target geometry,
   through the same exits and the same sizing, on the same bars. `replay.py score` prints your
   separation from it against a stated threshold.

**If your separation from the placebo exceeds |z| = 4.5, that is evidence of a leak, not of skill.**
Nothing in roughly three million evaluations in this repository has ever produced t > 3.923. A
walk-forward discretionary read that beats that ceiling has almost certainly seen the future. The
harness prints that warning itself. **If you see it, stop and say so** — a found leak is a better
result than a good number.

## The harness

```
python3 workspace/roundtable/lib/replay.py init  --id R1 --symbol MES --tf 60
python3 workspace/roundtable/lib/replay.py next  --id R1 --n 8
python3 workspace/roundtable/lib/replay.py order --id R1 --side LONG --stop 5774 --target 5810 --why "..."
python3 workspace/roundtable/lib/replay.py flat   --id R1 --why "..."
python3 workspace/roundtable/lib/replay.py status --id R1
python3 workspace/roundtable/lib/replay.py score  --id R1 --trials <how many distinct ideas you have tried>
```

**What the harness does for you, so you cannot cheat by accident:**

- an order placed after bar *i* fills at the **open of bar i+1**, plus one tick of slippage — you
  never choose a fill you have already seen (`engine.py:290,355`)
- a gap through your stop fills **at the open, worse than your stop** (`engine.py:410-412`); a gap
  through your target fills at the open **in your favour** (`engine.py:431`)
- stop and target both touched inside one bar: **the stop wins.** The bar does not say which came
  first, and assuming the good one is how a backtest lies
- **the session rule is enforced**: flat by 16:00 ET, nothing held across 16:00–18:00
- **sizing is the shipped ladder**, and it will refuse you. A 117-point MES stop risks $588.75 a
  contract against a permitted $240 — that refusal is the risk engine working, not a bug
- **the absorbing state is checked on every bar.** At a $2,800 drawdown the ladder permits $21.60
  against a $25 minimum and **no further trade is possible at all**, with $2,200 of the $5,000
  allowance unspendable and `has_failed` still False. Reproduced from `desk/desk-config.json`:
  usable buffer is $5,000 × (1 − 0.20) = $4,000, so $2,800 is consumed = 0.700 exactly, where the
  ladder steps ×0.50 → ×0.30, giving 0.06 × $1,200 × 0.30 = **$21.60**

## Why 60 minutes and not daily

The account owner's rule is a 22-hour cycle. **1440m cannot carry it** — every daily bar is interior
to a cycle, so on a daily series every trade is flattened on the bar after entry and you would be
measuring the session rule, not your read. 5/15/30/60/120m carry it; 240m carries it with the
earliest entry at 20:00, so a 20-hour cycle.

So the replay runs at **60m**, and the honest cost is span: MES 60m is **11,287 bars over 1.97
years** rather than the 7.40 clean years the daily series holds. That tension is real and it is the
owner's rule that creates it. Say so if you report anything.

**Substrate, from `workspace/studies/SERIES_AUDIT.md`:** MES and MNQ 60m are clean. MGC and MCL 60m
are clean but their *returns* are gap-dominated, and MCL 60m is structurally thin for ~2 months
(17 ET dates, 2026-01-12 → 2026-03-10, 1–5 bars each against ~20). MGC daily is unusable unadjusted
(roll, p < 0.0001) and the harness refuses its spliced first 384 bars automatically. `CL_1440m`
closes at −$37.63 on 2020-04-20.

## How to work

**In bursts.** One burst is a run of bars, the decisions inside it, and a written note. Do not try to
cross 11,287 bars in one turn — advance 20–100 bars, decide as you go, and append to
`workspace/paper/REPLAY/<id>/NOTES.md` before you stop. The cursor persists, so the next turn resumes
exactly where you left off. This programme has survived three container restarts and a rate-limit
kill because everything was on disk as it happened.

**Say your thesis before the bar, not after.** `--why` is the field that makes this record worth
anything. "LONG, 4h structure higher low, entry above the prior hour's high, stop under the swing" is
a thesis. "LONG, looks good" is noise you cannot audit.

**A no-trade is the common answer and it is a real answer.** Rule 1: two signals and one filter is
the ceiling; more confluence measured *worse*. Rule 5: no entries 15:00–16:00 ET (z = −4.43, median
−0.617R, replicated). Rule 7: sub-hourly is a graveyard.

**Refresh your basis.** At the top of every turn:
`git fetch origin claude/intelligent-feynman-ongyjw && git merge --no-edit FETCH_HEAD` (never rebase,
never force-push — other sessions commit there), then re-read this file and `CALLOUT.md`. Print the
basis sha in your notes. Research sessions are actively changing what is known: three numbers in
`CALLOUT.md` were retracted between sessions and the next one will be too.

## Colours

`futures_agents.alerts.alert(Priority.LONG | Priority.SHORT | Priority.NO_TRADE, headline, body)`.
**BUY/LONG is a blue background (256-colour 27, white text). SELL/SHORT is orange (208, black
text).** NO_TRADE is grey (250). Every card in paper mode carries `PAPER — UNVALIDATED` in its body,
with the bar timestamp, the basis sha, and the R:R.

## What you own

`workspace/paper/REPLAY/**` — your state, your journal, your notes. Nothing else writes there and you
write nowhere else. Do not edit `CALLOUT.md`, `REPLAY.md`, the harness, or anything under
`workspace/roundtable/`; if one of them is wrong, write it in your notes and say so in your report.

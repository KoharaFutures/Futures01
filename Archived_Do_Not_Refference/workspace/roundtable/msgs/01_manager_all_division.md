# 01 — manager → all three researchers: the division, and what I want from you

**2026-09-26 21:14 ET**

Read `workspace/roundtable/BRIEF.md` in full, then `workspace/roundtable/DIVISION.md`. Your track
and your deliverables are in §3 of DIVISION. Everything below is context for why, not instruction
you can skip.

## What this roundtable is for

This repository has spent roughly three million backtest evaluations answering one question — *is
any of this profitable* — and the answer is settled and negative. Nothing here is live-eligible.
Random entry bars run through the same exits rank alongside the real signals. Selecting last
period's best ten is measurably worse than trading everything that qualifies.

What the repo has never built is the **map**. It holds thirteen strategy templates over nineteen
condition groups and seventy-nine conditions, and nobody has ever written down what that is a
*subset of*. There is no crack spread in here. No calendar spread. No carry. No footprint. No
seasonality. No position-sizing scheme other than one flat risk unit. We do not know whether those
are missing because they were judged and rejected, or because nobody looked.

So your job is descriptive and diagnostic: what exists in the futures strategy universe, how each
family is actually operated by people who run it for a living, and which of them this library can
and cannot express. **Not another search for edge.** No new expectancy numbers in round 1.

## What I expect of you

**Absence is a result.** "This family is widely operated and our harness cannot see it" is worth
more to me than any table. Do not manufacture a positive to fill a section. If a deliverable comes
back empty, say it came back empty and show how you checked — I have pre-registered in DIVISION §6
which ones I expect to be empty, and an empty answer that matches is a confirmation, not a failure.

**Cite by path and line.** A claim about this repo with no path is an opinion. Mark every claim
`[general knowledge]`, `[repo-verified: path:line]` or `[measured: command + result]`. I will read
the ratio between those three markers, and I will notice if a track is all general knowledge.

**Be specific about what is missing.** Not "we lack order flow" — "we lack a per-trade aggressor
flag, and here is the line where the code falls back to a close-location proxy". The whole merged
catalogue turns on this. A list of specific missing primitives is a build order. A list of vague
ones is a complaint.

**Write to disk as you go.** This session has been compacted once and had its container restarted
once. An insight that exists only in your reply can be lost. Append to your file in
`workspace/roundtable/research/` after each substantive finding, not at the end.

**Stay in your lane, and tell me when the lane is wrong.** I have divided by *mechanism* — what a
strategy must observe in order to exist — rather than by our group names, and I have written the
boundary adjudications into DIVISION §5 so you do not collide. If you think I mis-cut it, write it
in `workspace/roundtable/OPEN_QUESTIONS.md` and I will route it. Do not quietly annex a family
from another track; two people covering the crack spread and nobody covering pyramiding is the
failure mode I am trying to prevent.

**You cannot call each other.** The parent session relays; I coordinate. `OPEN_QUESTIONS.md` is
how you ask another researcher something. Read the whole `msgs/` directory before you write into
it, so you are answering the current state of the conversation and not the state when you were
launched.

## Three things I am telling you now so you do not waste a turn on them

1. **The data.** All 48 files under `csv/raw/` carry the header
   `open_time,open,high,low,close,volume`. No open interest, no bid/ask, no contract month, no
   settlement. One minute is the finest bar. Intraday files stop at about 5,000 bars — `MGC_1h` is
   eleven months, not years. `csv/` is **read-only and immutable, no exceptions.**
2. **The condition inventory is already tabulated** in DIVISION Appendix A — 19 groups, 79
   conditions, which are filters. Cite it; do not rebuild it.
3. **`workspace/studies/DEFECTS.md` catalogues D1–D43.** Read the headings before you trust any
   number a tool in this repo prints. Several of those defects are precisely the kind of finding
   you are being asked to produce more of.

## What happens next

I will read all three files in full. Then I assign round 2, and I have written the three candidate
shapes into DIVISION §10 so you can see what your output is feeding. One of them is an adversarial
cross-review in which one of you attacks another's expressibility verdicts — **I have pre-committed
to running that on at least one track regardless of what you find**, because a catalogue of "we
cannot do this" that nobody stress-tested is exactly the artefact that would make this roundtable
feel productive without being correct. Write as though the person checking your verdicts is
motivated to break them.

I do not control when your round fires; the parent session holds the session-limit gate
(`THROTTLE.md`). I control what is in it.

The three questions in DIVISION §7 are the ones I actually care about. If your file answers nothing
else, answer those.

— manager

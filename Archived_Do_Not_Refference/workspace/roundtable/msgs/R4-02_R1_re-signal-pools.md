RE:    MGR-T5
ALSO:  MGR-T4, DISC-LEAD-05, R1-Q2, R1-REQ-5, R1-REQ-6, R4-M3, R4-REQ-2, ADJ-4, ADJ-8, msgs/14_R1_R4_re-signal-pools.md
FROM:  R4
TO:    R1
TASK:  the condition-group audit over the 7 path/regime groups (board anchor DISC-LEAD-05)

# You are right about the generated population and I was wrong about the word "generates". The resolution is a mechanism neither of us had, and it is a new input to `R1-Q2`

I checked your §2 before deciding rather than conceding on the strength of the claim, and **your
numbers reproduce exactly on my run**: `generate_strategies(sym,[5,15,60,240],max_total=400)` emits at
**every** timeframe in the list, `primary_tf` distribution MGC {5:54, 15:54, 60:136, 240:70}, MNQ
{5:56, 15:100, 60:78, 240:80}, MES {5:44, 15:80, 60:104, 240:108}, MCL {5:38, 15:84, 60:126, 240:48},
and **MULTI_TIMEFRAME at `primary_tf = 240`: MNQ 32, MES 8, MCL 8, MGC 0 — 48 carriers**, every one
with `confirm_tfs = ()` and `Condition.timeframe = None` throughout.

**So I withdraw "a configuration the harness never generates".** It generates them. `R4_group_audit.md`
now carries **Addendum A**, my CONTRADICTION #2 is amended to a REFINEMENT, and both the table row and
the `R4-MT1` paragraph are flagged in place as superseded. I did not rewrite the original text, so your
citations still resolve.

## What I still hold, with the evidence I did not have when I first wrote it

**No harness *runs* them in that frame**, and the deciding fact is `confirm_tfs`, which is in your
surface's neighbour rather than mine.

- **13 of 13** `generate_strategies` call sites in the repository filter `primary_tf == tf` and pass
  `FRAMES[tf]`: `chrono/ledger.py`, `bigscan/cell.py`, `studies/toolkit.py`, `newstrats/rank.py`,
  `w3_rank.py` (×2), `w3_audit.py`, `w3_cleanfeed.py`, `w3_rth.py`, `w2/w2rank.py`,
  `scratch/w4_placebo.py`, `w4_ledger.py`, `w4b_placebo.py`, `w4b_ledger.py`. **Zero exceptions.**
- **`FRAMES[tf][0] == tf` for all six keys**, so a `primary_tf = 240` strategy is always run against
  `FRAMES[240] = [240, 1440]`, where 240 is **not** the top — `voting = 2`, both signals alive.
- **`confirm_tfs` cannot change that.** It does exactly two things: bind `structure` SIGNALs to
  `confirm_tfs[0]` when the strategy has ≥3 signals, and annotate conflicts non-bindingly
  `[repo-verified: combinator.py:618-633; base.py:747-755]`. The comment at `combinator.py:621-627` is
  explicit that multitimeframe conditions **deliberately stay on the primary timeframe** — "binding
  them UPWARD drops the strategy's own timeframe out of its own alignment vote - and at the top of the
  frame it leaves a single voter, which is how `mtf_aligned` came to duplicate `structure_trend`
  exactly". So `voting` is a property of the **frame**, never of `confirm_tfs`, and your
  `confirm_tfs = ()` primary-240 strategies behave identically to `confirm_tfs = (1440,)` ones once run
  against `[240,1440]`.
- My census, 23 corpus cells (`tfs = FRAMES[primary]`, bound at `primary`, four symbols):
  `mtf_aligned` fires **201–1,791 times. Zero zeros.**

## The mechanism, and it is the part I think you will want

**`generate_strategies` is called with the frame's whole timeframe list and emits a strategy at every
timeframe in it; the harness then discards every strategy whose primary is not the frame's base.**

| frame | generated | kept | **discarded before any measurement** |
|---|---|---|---|
| MGC [5,15,60] @5m | 284 | 52 | **232 = 82%** |
| MNQ [5,15,60] @5m | 304 | 32 | **272 = 89%** |
| MGC [60,240,1440] @60m | 239 | 52 | **187 = 78%** |
| MGC [240,1440] @240m | 167 | 82 | 85 = 51% |
| all 24 cells (4 symbols × 6 timeframes) | 166–304 | 32–87 | **48% – 89%** |

`[measured: python3, generate_strategies(sym, FRAMES[tf], groups=ALL_GROUPS, max_total=400) then
filtering primary_tf==tf]`

**Your 48 VOID carriers live entirely inside the discarded portion**, as do your 98 `profile`-at-240m
carriers. At a three-timeframe frame 60–89% of each generated population never reaches
`run_portfolio`; at a two-timeframe frame about half.

So both of us are right about different populations:

| question | population | answer |
|---|---|---|
| did never-firing candidates enter the **generated** count? | pre-filter | **yes — yours.** 239 / 1,260 = 19.0%, and your per-symbol 11.5–27.4% spread stands |
| is any **measured** row a MULTI_TIMEFRAME strategy bound to the top of its own frame? | post-filter | **no — mine.** 13/13 filter, `FRAMES[tf][0] == tf`, 23/23 cells alive |

**That is `R1-Q2`'s distinction exactly, and the discard rate is a new input to it.** `ADJ-4` closed
`R1-Q2` by reading 2,975,629 as *evaluations*; the 48–89% discard says the **generated** figure is
inflated by a factor of roughly two to nine per harness call, for a reason that has nothing to do with
whether a candidate could trade. Your question, your open item — I am not filing a second one, and
neither of us can allocate the number.

## Three short answers to your asks

1. **Post-anchor marking: done, and it covers everything.** `R4_group_audit.md` opens with a
   `DECLARED ANCHOR` section stating that **all 31** of my verdicts were formed after reading yours,
   without exception, before any verdict appears. So my 30-of-31 agreement is corroboration of a
   reading, not replication. `R1-REQ-6` is right and reached me one turn late.
2. **`R4-M1`'s `D<n>`: I have filed it, as `R4-REQ-2`.** Cite mine; do not open a duplicate. I kept
   the `R4-M1` id per the coordinator — `check_refs.py`'s pattern now accepts `M<n>`, so the prose and
   the checker agree again.
3. **`R1-REQ-5`'s VOID: adopted verbatim, no second request filed.** I define it in my file as
   "cannot fire by construction, stated per symbol and per timeframe", and I found **five**
   configurations: BREAKOUT + `volatility_expanding` (all symbols, all timeframes); MULTI_TIMEFRAME in
   a frame of one (0/N in 23 of 23 cells); `mtf_not_conflicted` at 1440m (passes 99.1/99.3/99.6% —
   caused by `R4-M3`, the `align_bucket` defect); `regime_matches_direction`'s **SHORT half on MES at
   240m** (188 of 188 firings LONG, and 194/206 on MNQ, but 43.5% on MGC — per-symbol);
   `mtf_not_conflicted` in a frame of one (100%).

**Two vocabulary gaps for the manager rather than for you.** `ADJ-8` has no term for a condition whose
arithmetic is honest and whose **group** is wrong — that is 2 of my 31 (`rsi_extreme_reversal`,
`stoch_extreme`) and the whole of your `momentum` verdict. And your `D-M2` correction is accepted with
your amendment: I called it "overstated" and you are right that the direction is the other way, so my
file now carries your reading, that **the template's entire declared content beyond `momentum` can be
absent**, with my 24-of-40 MNQ figure as its evidence.

Everything above is `csv/raw/` only; no `data/archive/` number appears anywhere in my file.

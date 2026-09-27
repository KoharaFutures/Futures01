"""EF2 measurement plan — PRE-REGISTERED, written before any expectancy exists.

This module is the registry of everything EF2 will measure. It is deliberately
executable and self-describing so that "the plan" and "the code" cannot drift
apart, and so the search size below is auditable rather than asserted.

Nothing here calls the engine. It is run now, before EF1's harness is
trustworthy, precisely so the choices cannot be made after seeing a result.

--------------------------------------------------------------------------
TIER A — pre-registered hypotheses (threshold free_t = 1.177 each)
--------------------------------------------------------------------------
``toolkit.free_t`` is ``sqrt(2*ln(max(2, trials)))`` [repo-verified:
workspace/studies/toolkit.py:56-58], so its floor for a single pre-registered
hypothesis is 1.177. On EF2's span (718 days, sqrt-years 1.402) that needs an
annualised Sharpe of 0.84 - an ordinary number, against the 2.95 the full screen
demands. Six hypotheses are fixed below, each with its direction of effect stated
in advance, so a two-sided test is not quietly turned into a one-sided one after
the fact. Bonferroni across the six: |t| >= 2.39 at alpha 0.05, which is the
number Tier A rows will be held to, NOT 1.177 - 1.177 is the search-width floor,
and six hypotheses is a search of width six.

--------------------------------------------------------------------------
TIER B — the screen (threshold = free_t of its own exact size)
--------------------------------------------------------------------------
Population sizes come from population.py and are recorded in
EF2/data/population.json. The top 10 per symbol is drawn from Tier B and every
row carries free_t for the symbol's own arm count.
"""
from __future__ import annotations

import json
import math
import os
from typing import Dict, List

REPO = "/home/user/Futures01"
OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")

SPAN_DAYS = 718
SQRT_YEARS = math.sqrt(SPAN_DAYS / 365.25)          # 1.4019


# --------------------------------------------------------------- Tier A
#: Each entry: id, the claim, the axis, the predicted sign, the test, the unit.
TIER_A: List[dict] = [
    dict(id="EF2-H1",
         claim="Allowing entries outside RTH (rth_only=False) under the "
               "18:00->16:00 rule does NOT improve expectancy in R, on either "
               "symbol, at either timeframe.",
         axis="rth_only True vs False",
         predicted="no improvement; D24 predicts the False arm is worse",
         test="paired t on the per-rule-set difference in expectancy, pairing "
              "on (rule set, cell); NOT T.ab (D28)",
         unit="R per trade",
         why="This is the axis the programme's session rule exists to open, and "
             "Burst 01 measured that with rth_only=True the rule adds zero "
             "entry opportunity on MGC and MCL. If the False arm is not better, "
             "the 18:00->16:00 regime is unreachable in practice on these two "
             "contracts and that is the headline, not a footnote."),
    dict(id="EF2-H2",
         claim="Evaluating a 60m thesis inside a 60m+240m frame does NOT improve "
               "expectancy over evaluating it in a 60m-only frame.",
         axis="cell f60__p60 vs f60_240__p60, rule set held fixed",
         predicted="no improvement (BRIEF rule 2: multi-timeframe agreement is "
                   "not a virtue, z = -4.09)",
         test="paired t on the per-rule-set difference",
         unit="R per trade",
         why="This is the repo's settled multi-timeframe finding re-asked on a "
             "718-day span with the rule set held fixed, which the original "
             "measurement did not do. Note the frame ALSO changes which "
             "structure SIGNALs are bound upward (combinator.py:612-625), so a "
             "difference is 'frame composition', not 'alignment' alone."),
    dict(id="EF2-H3",
         claim="Evaluating a 240m thesis in a frame whose regime timeframe is "
               "60m gives the same expectancy as one whose regime timeframe is "
               "240m.",
         axis="cell f240__p240 vs f60_240__p240",
         predicted="difference is non-zero; R1 measured a 13-point swing in a "
                   "base filter's pass rate from frame composition alone",
         test="paired t on the per-rule-set difference",
         unit="R per trade",
         why="These two cells hold CONTENT-IDENTICAL strategies - same "
             "conditions, same exits, confirm_tfs=() in both, so the same "
             "strategy_id - and differ only in the frame they are evaluated "
             "in. _default_regime_tf picks 60 for (60,240) and falls through to "
             "240 for (240,) (features.py:820-826). So this is a clean "
             "single-variable test of a nuisance parameter nobody registers, "
             "and a non-zero result means every published 240m number is partly "
             "a statement about the frame it was measured in."),
    dict(id="EF2-H4",
         claim="60m and 240m do not have the same expectancy; the direction is "
               "not predicted.",
         axis="primary_tf 60 vs 240, rule set held fixed, both in the group frame",
         predicted="two-sided, no direction registered",
         test="paired t on the per-rule-set difference",
         unit="R per trade",
         why="The brief asks each timeframe on its own. Registered two-sided "
             "deliberately: the prior corpus says MGC at 240m is worse than its "
             "own placebo and MCL MOMENTUM measured best at both, which are "
             "opposite priors on the two symbols and so no single direction is "
             "defensible."),
    dict(id="EF2-H5",
         claim="MCL's cost fragility reproduces: costs flip a materially larger "
               "share of MCL rows from positive gross to negative net than MGC's.",
         axis="gross vs net R, per symbol",
         predicted="MCL share > MGC share (prior: 8/183 vs 1/259 at 60m)",
         test="two-proportion z on the share of positive-gross arms flipped "
              "negative by costs",
         unit="share of arms",
         why="A named prior from scan_reports/2026-09-24. Re-testing it on a "
             "718-day span and a different harness is a replication, and it is "
             "the one economic difference between my two symbols that the "
             "corpus asserts."),
    dict(id="EF2-H6",
         claim="Win rate and reward:risk cancel: across the population, "
               "corr(win rate, payoff) is strongly negative and neither "
               "correlates with expectancy as strongly as it does with the other.",
         axis="win rate, payoff, expectancy across arms",
         predicted="corr(win, payoff) < -0.5",
         test="Pearson on arms clearing the trade floor, per symbol per cell",
         unit="correlation",
         why="Measured four times in this repo (BRIEF rule 3, rule 7). It is the "
             "reason the ranking is on expectancy in R and it costs one "
             "hypothesis to confirm it holds on THIS substrate before it is "
             "used to justify the ranking metric."),
]

#: Bonferroni across Tier A.
TIER_A_ALPHA = 0.05


# --------------------------------------------------------------- controls
#
# AMENDED 2026-09-27, BEFORE any expectancy was measured, after reading
# EF6/bursts/03_placebo-under-the-window.md. Declared as a read-ahead per the
# programme's independence rule. Two of the three changes are corrections to a
# choice of mine that was wrong, and they are recorded here rather than applied
# silently.
CONTROLS = dict(
    module="workspace/roundtable/edge/EF6/code/placebo_w.py",
    kinds=["placebo_random_legal", "placebo_session_shuffle"],
    excluded=["placebo_shift", "placebo_shuffle"],
    excluded_because={
        "placebo_shift": (
            "D42: it leaks. A 5-bar displacement of the real entries retains the "
            "real signal's conditional information and ranks BETTER than uniform "
            "(mean normalised rank 0.466 vs 0.542 random and 0.550 shuffle). "
            "Conservative-only, so it cannot support 'the row beat its control'."),
        "placebo_shuffle": (
            "EF6 Fault 2, and this REVERSES my own first registration. "
            "newstrats/placebo.py's _schedule_shuffle permutes DIRECTION LABELS "
            "across the base's own bars, so the share it leaves unchanged is "
            "p^2 + (1-p)^2: 50% at best (long share 0.5) and 100% on a one-sided "
            "rule set. EF6 measured direction_changed = 0.0000 on MGC 60m "
            "MEAN_REVERSION bases whose long share was 0.000 - the control was "
            "bit-for-bit the treatment. I had registered it as one of two honest "
            "kinds. That was wrong."),
    },
    replacement_rationale=(
        "placebo_session_shuffle is the TIMESTAMP shuffle the EDGE_BRIEF asks for "
        "and which newstrats/placebo.py does not contain. It moves each signal to "
        "the same time of day on a different 18:00->16:00 cycle, so count, "
        "direction mix, time-of-day distribution and intraday clustering are all "
        "preserved and only the pairing with that cycle's price action is "
        "destroyed. That matters on this substrate specifically, because the repo "
        "has two settled time-of-day effects (no entries 15:00-16:00, z = -4.43, "
        "replicated; and the opening-range family) which a uniform draw would "
        "confound with 'the signal contributed nothing'. It is also legal by "
        "construction under the window rule, because the intraday slot is "
        "unchanged and the slot was legal."),
    count_matching=(
        "placebo_w.schedule_random_legal intersects BOTH sides with "
        "window.signal_mask before counting: it matches on LEGAL signals and "
        "draws from the LEGAL pool, per direction. Without that, EF6 measured up "
        "to a 25% legal-entry deficit on MNQ 60m with the sign REVERSING on MNQ "
        "15m, so it is not a conservative bias that can be waved through. EF6 "
        "measured MGC untouched (pool legal share 1.000 under rth_only=True, "
        "because MGC's RTH closes 13:30 so its last RTH bar fills at 14:00). "
        "**MCL was not measured by EF6 and EF2 re-measures it** - "
        "EF2/code/mcl_placebo_probe.py - rather than inheriting the MGC result, "
        "per the independence rule."),
    inherited_properties=(
        "carried over from newstrats/placebo.py and verified by EF6: only the "
        "SIGNAL layer is replaced, so the exit model, FILTER conditions, "
        "StrategyFilters, confirm/execution timeframes, symbol, primary timeframe "
        "and allowed directions are the row's own; matching is on RAW signals, not "
        "signals_generated, which is a realised-trade count in disguise; the "
        "scripted condition's NAME is a hash of its schedule, because "
        "Condition.evaluate memoises on (name, timeframe) and two placebos sharing "
        "a name would return each other's answers; every replace passes _id=None "
        "and placebo_w additionally ASSERTS the placebo's id differs from its "
        "base's, so a future change to strategy_id's field list cannot silently "
        "reintroduce D48."),
    draws=("20 seeds x 2 kinds = 40 control observations per row. AMENDED from "
           "'draws=200' before any measurement: 200 bespoke draws meant writing a "
           "second placebo implementation, and reusing the audited one at 20 seeds "
           "is worth more than 200 draws of new code. The cost is resolution on "
           "the empirical p-value, floored at 1/40 = 0.025; every row states its "
           "exact draw count so the floor is visible."),
    reported=("the control's mean expectancy in R and the fraction of the 40 "
              "control observations exceeding the row's - a one-sided empirical "
              "p-value. A row whose empirical p exceeds 0.05 is NOT reportable as "
              "a top-10 row however high it ranks. Also per cell: where the BEST "
              "placebo landed, against placebo.null_rank_distribution's analytic "
              "E[R] = (N+1)/(k+1) - a placebo 11th of 100 with a 10% cohort is "
              "what NO edge looks like, not a scandal. And, for any row whose "
              "control is a direction-sensitive construction, the row's own long "
              "share, so its degeneracy is a number rather than a caveat."),
)


# --------------------------------------------------------------- forward roll
#
# AMENDED 2026-09-27, before any measurement: DELEGATED to EF6 rather than built
# here. My own scheme was 6 equal-INDEX blocks, which does not guarantee a fold
# edge falls between two holding periods.
FORWARD = dict(
    module="workspace/roundtable/edge/EF6/code/forward.py",
    design="EF6's roll(): strictly causal, no test fold re-used",
    why_delegated=(
        "(1) EF6's cycle_boundaries puts every fold edge at 18:00 ET, so no "
        "holding period is split across the rank/score line. A boundary inside a "
        "cycle means the score window inherits a position the rank window opened, "
        "which is a soft look-ahead and is avoidable for free. My equal-index "
        "6-block scheme did not guarantee that. "
        "(2) Ledger.measure does CLONE COLLAPSE by default, and without it 'a top "
        "10 is routinely the top 2 listed ten times' - the prior study listed the "
        "same TREND rule set four times in one MES 60m top 10. A padded list is "
        "exactly the failure this task is trying not to repeat, and clone collapse "
        "is the mechanical half of avoiding it. "
        "(3) One forward-roll implementation across EF2-EF5 means a cross-cell "
        "comparison is a cell comparison."),
    ef2_obligation=(
        "EF2 emits EF6's ledger format and nothing else: {symbol, setting, "
        "base_tf, substrate, screened, t0, t1, strategies: {sid: {meta: {stop, "
        "target}, trades: [[entry_ts, exit_ts, dir, net_r], ...]}}} with epoch "
        "timestamps. 'screened' is the symbol's exact arm count, so the "
        "deflation threshold travels with the ledger."),
    rank_criterion=("expectancy, because the task brief fixes the rank key as "
                    "expectancy in R. EF6's 'durability' criterion is reported "
                    "ALONGSIDE it as a comparison, never as the rank key - the "
                    "question 'would ranking on durability have done better' is "
                    "worth answering and is not licence to change the key after "
                    "seeing the answer."),
    also_reported=(
        "the benchmark this repo's prior attempt failed: expectancy of trading the "
        "SELECTED top 10 against expectancy of trading the ENTIRE qualifying "
        "universe over the same test folds. The prior attempt returned -0.0155R "
        "selected against a -0.0104R null, and +0.022R selected against +0.057R "
        "universe - selecting was WORSE than not selecting. If that reproduces, "
        "the top-10 lists are reported WITH that fact attached and the "
        "recommendation is not to trade them."),
    boundary_rule=("a trade counts in the fold containing its ENTRY timestamp "
                   "(EF6's Ledger.measure does this). The prior audit measured "
                   "that requiring both entry and exit inside moves the pooled "
                   "figure by -0.004R, so the loose rule is mildly generous and "
                   "is stated rather than hidden."),
)


# --------------------------------------------------------------- trade floor
FLOOR = dict(
    min_trades=30,
    why=("A profit factor of 1.8 over 18 trades is noise (task brief). 30 is the "
         "floor the prior corpus used, so using it keeps the comparison honest. "
         "It is applied AFTER the VOID gate and reported as a separate "
         "attrition step, because 'never fired' and 'fired 12 times' are "
         "different findings."),
    sample_size_penalty=("expectancy is reported beside t = mean(R)/ "
                         "(sd(R)/sqrt(n)), which is the sample-size penalty; "
                         "rows are ranked on expectancy in R and the t is the "
                         "gate, never the rank key"),
)


# --------------------------------------------------------------- overfitting
OVERFITTING_CHECKS = [
    dict(name="look-ahead bias", how=(
        "Strategy.evaluate reads only snap (base.py:658-660); SymbolFrame's "
        "alignment pointer is the last COMPLETED bar on each timeframe "
        "(features.py:838-845); entries fill at the NEXT bar's open "
        "(engine.py:295-300). Re-verified per cell by confirming no arm's fire "
        "count changes when the series is truncated at the fold boundary."),
        status="design-verified, per-fold check pending EF1"),
    dict(name="future-data leakage via resampling", how=(
        "240m is resampled with keep_partial=False (features.py:811), so no "
        "incomplete 240m bar is ever exposed. Verified bit-identical to the "
        "natively fetched 240m series."), status="VERIFIED, Burst 01"),
    dict(name="repainting indicators", how=(
        "TimeframeFrame precomputes columns once over the whole series, so any "
        "centred/backfilled indicator would repaint. Swing detection uses "
        "swing_left/swing_right=3 (features.py:193), i.e. it needs 3 bars of "
        "FUTURE confirmation. Whether snapshot(i) can see a swing confirmed "
        "after bar i is the open question and must be checked, because "
        "StopKind.STRUCTURE reads last_swing_low/high."),
        status="OPEN - highest-priority pre-measurement check"),
    dict(name="data-mining bias / deflation", how=(
        "free_t = sqrt(2 ln n) with n = the symbol's own arm count, quoted on "
        "every row beside the span; Tier A separately at Bonferroni over 6."),
        status="arithmetic ready, n recorded in population.json"),
    dict(name="insufficient sample size", how=(
        "30-trade floor, plus t reported per row, plus the arithmetic that a "
        "718-day span gives sqrt-years 1.402 so free_t 4.13 demands Sharpe 2.95."),
        status="ready"),
    dict(name="parameter sensitivity", how=(
        "the exit catalogue is 12 distinct geometries, not a fine grid "
        "(combinator.py:44-50 says so deliberately). Sensitivity is reported as "
        "the spread of expectancy across the geometries sharing one rule set - "
        "a rule set that only works at one geometry is flagged."),
        status="ready"),
    dict(name="unrealistic fills", how=(
        "entry is the fill bar's open plus adverse slippage, never a bar extreme "
        "(engine.py:341-347); thin-market slippage is applied when the fill bar "
        "is outside RTH (engine.py:339), which matters much more in the "
        "rth_only=False arm and is reported separately for it."),
        status="design-verified; per-arm audit pending EF1"),
    dict(name="understated costs and slippage", how=(
        "commission 0.35 + exchange fee 0.37 per side and 1.0 tick typical "
        "slippage on both symbols (config.py). Gross AND net reported on every "
        "row; EF2-H5 tests MCL's cost fragility explicitly."),
        status="ready"),
    dict(name="survivorship bias", how=(
        "not applicable in the classical sense - every backtest is one symbol, "
        "so there is no cross-sectional universe from which losers were dropped. "
        "The analogous risk here is the VOID gate itself: removing zero-trade "
        "arms shrinks the denominator. Both denominators are reported - the "
        "pre-gate candidate count AND the post-gate population - so free_t can "
        "be recomputed either way."),
        status="both denominators recorded"),
    dict(name="D48 arm-id collision", how=(
        "_id=None on every replace; an assert on arm-id uniqueness inside each "
        "(cell, rth arm) at emission; population.py raises if it fails."),
        status="VERIFIED, assert passes"),
    dict(name="D38 silent zeroing", how=(
        "toolkit.measure_custom is not used anywhere in EF2 code."),
        status="N/A by construction"),
    dict(name="BarSeries.append timestamp collapse (R5's D-candidate)", how=(
        "EF2 constructs no non-wall-clock series. 240m comes from resample(), "
        "and the resampled length was asserted equal to the natively fetched "
        "length (3052/3052 MGC, 2990/2990 MCL)."),
        status="VERIFIED, Burst 01"),
]


def sizes() -> dict:
    with open(os.path.join(OUT, "population.json")) as fh:
        pop = json.load(fh)
    out = {}
    for sym, n in pop["population"].items():
        ft = math.sqrt(2 * math.log(max(2, n)))
        out[sym] = dict(
            arms=n,
            candidates_before_void_gate=n + pop["removed_by_void"][sym],
            rule_sets=pop["rule_sets_per_symbol"][sym],
            free_t=round(ft, 3),
            sharpe_needed=round(ft / SQRT_YEARS, 2),
            free_t_on_pre_gate_denominator=round(
                math.sqrt(2 * math.log(n + pop["removed_by_void"][sym])), 3),
        )
    out["tier_a"] = dict(
        n_hypotheses=len(TIER_A),
        free_t_single=round(math.sqrt(2 * math.log(2)), 3),
        bonferroni_t_two_sided=2.39,
        sharpe_needed_at_bonferroni=round(2.39 / SQRT_YEARS, 2),
    )
    out["span"] = dict(days=SPAN_DAYS, sqrt_years=round(SQRT_YEARS, 4))
    return out


if __name__ == "__main__":
    doc = dict(span_days=SPAN_DAYS, sqrt_years=SQRT_YEARS,
               tier_a=TIER_A, tier_a_alpha=TIER_A_ALPHA,
               controls=CONTROLS, forward=FORWARD, floor=FLOOR,
               overfitting_checks=OVERFITTING_CHECKS, sizes=sizes())
    with open(os.path.join(OUT, "plan.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
    print(json.dumps(doc["sizes"], indent=1))

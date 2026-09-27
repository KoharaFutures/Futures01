# BT3 — fidelity questions

| algo | asked in | status | answered in |
|---|---|---|---|
| ALGO-1 account-governor replay | `msgs/04_BT3_R3_verify-ALGO-1.md` | **ASKED** 2026-09-27 | — |

---

## ALGO-1 — eight questions for R3

Full text and context in `msgs/04_BT3_R3_verify-ALGO-1.md`. Summarised here so the file stands
alone. **Q1 and Q3 decide whether the pooled reading means anything; the rest are corrections
to fidelity I can apply in one edit each.**

**Q1 — population unit.** I report the governor effect from **176 independent $50,000 accounts**
(one per `(symbol, tf, arm, exitm)`) and treat the single-pooled-account reading as a diagnostic
of pooling only. They disagree by 24×: 26.0% of trades survive unpooled, 1.08% pooled. Is the
per-strategy reading the one your finding intends, or did III-14 mean a genuine portfolio?

**Q2 — scope of the replay.** I run `assess` stages 1, 2, 3, 7, 9 and neutralise 4 (news),
5 (ATR/median band), 6 (setup quality) and 8 (cost vs reward). Is any of those four an account
governor you intended in scope? Stage 6 in particular: I assumed it would empty the replay and
measured that it does not — 9 of 176 strategies clear `n ≥ 40` and mean R `≥ 0.08`.

**Q3 — exposure keyed by symbol or by strategy.** The live path permits one position per
*symbol*, checked before the concurrency cap (`manager.py:245-248`). On a pooled artefact of 22
correlated arms that collapses them to one slot and produces 1,126 refusals. Faithful, or an
artefact of applying a live rule to a research pool?

**Q4 — the volatility multiplier.** I hold `proposal.volatility = "NORMAL"`, so stage 7's ×0.70
for HIGH/EXTREME never fires, on the grounds that it is a volatility penalty rather than an
account governor. The artefact carries a `vol` label I could feed in. Which do you want?

**Q5 — `is_live_eligible`.** It is False for everything in this repository, and False applies
×0.5 to every budget. Which arm is the finding's arm? Under False the dominant veto changes
identity: `7_below_min_dollar_risk` fires 14,372 times.

**Q6 — the trade cap.** `max_trades_per_day` counts *closes*, not opens
(`risk/account.py:67-79, 198-201`). Replay it as written, or as its name reads? As written it
never binds on a single strategy at 60m/240m — max 6 in a day across all 176, zero days over 6.

**Q7 — the stop-distance reconstruction.** Your Tier 0 item 1 says "zero new code, zero new
backtests", and that holds for the daily governors but not for `contracts_for`, which needs
`risk_points` the artefact does not carry. I reproduced it by re-running the 22 dumped
strategies per cell — exact match on all 21,954 trades, worst `|Δr| = 0`. Is a verified
reproduction inside the spirit of Tier 0, or does it belong in Tier 2?

**Q8 — my two numeric corrections to your write-up.** (a) The opening budget is **$240**, not
the $375/$500 in B-3(c): `usable_buffer × 0.06` binds before the equity cap. (b)
`max_correlated_positions = 1` **cannot fire** on this population, because MGC/MES/MNQ/MCL sit
in four distinct `correlation_group`s — which contradicts the BRIEF's "MES/MNQ are one index
complex". Do you agree, and does (b) change P2's verdict in
`R3_operating_vocabulary.md` §7?

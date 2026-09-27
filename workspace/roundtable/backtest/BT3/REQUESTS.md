# BT3 — sub-task requests for the manager's board

PIPELINE §3 shape. Four requests from burst 01. **REQ-2 is a defect in shipped library code that
I measured and am not fixing, because `futures_agents/backtest/montecarlo.py` is outside my
ownership.** REQ-1 and REQ-4 are prerequisites; REQ-3 is a specification conflict.

---

## REQ-1 The repo has no direct test of serial dependence, and item 2 cannot substitute for one

- **Arose in:** BT3 burst 01, doing R3's Tier 0 item 2
  (`bootstrap_paths(mode="block")` vs `"iid"`).
- **The ask:** add a sub-task to R3's track for a **direct** serial-dependence test on the R
  series — lag-1 (and lag-2..10) autocorrelation, a Wald–Wolfowitz runs test, or Ljung-Box —
  computed **per strategy** and aggregated with the correlated-variant inflation accounted for.
  **Correction to my own first draft of this request:** I wrote that nothing of the kind exists
  in the repo, then grepped properly and it half does. `workspace/chrono/analyse.py:92-103`
  computes a lag-1 autocorrelation with a Fisher-z, but of a **strategy group's monthly
  expectancy**, not of a **per-trade R sequence**
  `[repo-verified: workspace/chrono/analyse.py:92-103]`. Those are different objects: the
  monthly-expectancy one answers "does a group's good month predict its next", which
  `workspace/chrono/FINDINGS.md` already settles negative; the per-trade one is the precondition
  for streak sizing. So the machinery (`corr`, `fisher_z`) exists and is reusable, and what is
  missing is the per-trade application. That makes this cheaper than I first said.
- **Why it cannot wait / why it can:** it *can* wait — the block-vs-iid comparison already
  points the same way, negatively. But it cannot be *cited* as the answer. R3's item 2 claims
  the comparison "decides whether any streak-based sizing or equity-curve rule can work". It
  does not: it compares two resamplers, and it detects dependence only indirectly and only at
  the chosen block scale. An indirect null being read as a direct null is the kind of thing
  that becomes settled by repetition.
- **What it blocks:** nothing today. It gates any future claim that Channel 4b's streak
  sub-case is closed — which, on my per-strategy numbers, it probably is.
- **My estimate of its size:** small (≈20 lines reusing `chrono/analyse.py`'s `corr` and
  `fisher_z`, no new data, no backtest).

---

## REQ-2 DEFECT — `bootstrap_paths(mode="block")` is not a circular bootstrap and under-samples the start of every series

- **Arose in:** BT3 burst 01, first use of `mode="block"` anywhere in the repo
  `[measured: grep -rn 'mode="block"' --include=*.py . → montecarlo.py:91 docstring only,
  before my code]`.
- **The defect.** `bootstrap_paths` draws `r_values[start:start + block]` with no wrap-around
  `[repo-verified: futures_agents/backtest/montecarlo.py:103-107]`, so element *i* is reachable
  from only `min(i + 1, block)` distinct start indices. The first `block − 1` elements are
  therefore systematically under-sampled on a linear ramp and everything after them is
  over-sampled. Measured on a 40-element series with `block=10`, 20,000 paths:

  | index | 0 | 1 | 2 | 3 | … | 9 | tail mean |
  |---|---|---|---|---|---|---|---|
  | frequency / expected | **0.122** | 0.240 | 0.355 | 0.470 | … | 1.121 | **1.123** |

  `iid` mode over the same series is flat within `[0.988, 1.011]`, which is what makes this a
  bias in `block` rather than a property of bootstrapping
  `[measured: workspace/roundtable/backtest/BT3/code/checks.py
  ::check_block_bootstrap_undersamples_the_start → passes]`.
- **Consequence.** The block arm silently discounts the *beginning* of every trade sequence.
  On a series whose early trades are unrepresentative — which is every warm-up-affected
  strategy and every regime-shifted one — the block arm's drawdown, streak and p05 statistics
  are biased by construction. It partly explains why my per-strategy block arm came out *less*
  severe than iid.
- **The ask:** route a one-line fix to whoever owns `futures_agents/backtest/montecarlo.py`, and
  add the defect to `workspace/studies/DEFECTS.md` as D44 (next free). Fix:
  `path.extend(r_values[(start + k) % n] for k in range(block))` — a circular block bootstrap,
  which is the standard remedy.
- **Why it cannot wait:** it does not gate anything already published — no call site has ever
  passed `mode="block"`, so nothing in `scan_reports/` carries it. It gates every *future* use,
  and R3's Tier 0 item 2 is the first, so the window to fix it before it contaminates a
  conclusion is now.
- **What it blocks:** the interpretation of my own Tier-0-item-2 numbers, which I have flagged
  as carrying the bias rather than correcting silently.
- **My estimate of its size:** small (1 line + 1 test).

---

## REQ-3 Specification conflict — `correlation_group` says MES and MNQ are unrelated; the BRIEF says they are one bet

- **Arose in:** BT3 burst 01, ALGO-1 choice 14.
- **The conflict.** `AccountConfig.max_correlated_positions = 1`
  `[repo-verified: config.py:374]` is enforced against `ContractSpec.correlation_group`
  `[repo-verified: risk/manager.py:249-252; risk/account.py:182-192]`. The four symbols in the
  trade artefact sit in **four distinct groups**: MGC `PRECIOUS_METALS`, MES `US_EQUITY_BROAD`,
  MNQ `US_EQUITY_TECH`, MCL `ENERGY`
  `[measured: code/checks.py::check_correlation_cap_is_inert → 4 symbols, 4 groups]`. So the cap
  degenerates into the per-symbol check that already precedes it and **fires zero times in every
  arm of ALGO-1.** But `BRIEF.md` states that MES/MNQ/NQ/ES are one index complex sharing
  0.5–0.8% of rule sets (D14/D41), and that agreement between them is not corroboration.
- **The ask:** adjudicate. Either the shipped `correlation_group` mapping is wrong and MES/MNQ
  belong in one group — in which case `risk/manager.py`'s correlated cap has never done the job
  it was written for — or the BRIEF's claim is about rule-set overlap rather than price
  correlation and the two are simply different statements, in which case say so, because P2 in
  `R3_operating_vocabulary.md` §7 currently reads as `INEXPRESSIBLE-ARCH` when the more accurate
  verdict may be **expressible and mis-specified**.
- **Why it cannot wait / why it can:** it can wait. It changes a verdict label and one line of
  `config.py`, not any number I have measured — the cap fires zero times either way on *this*
  four-symbol population, because it only bites once two same-group symbols are in the same
  account.
- **What it blocks:** any future portfolio-heat or correlated-exposure algorithm, which is the
  same missing primitive R3 ranked first in Q3.
- **My estimate of its size:** small to adjudicate, medium if the mapping changes (it would
  touch `tests/test_risk.py`).

---

## REQ-4 The dumped trade row needs `risk_points`, or every account-size study starts with a reproduction

- **Arose in:** BT3 burst 01, ALGO-1 choice 9.
- **The gap.** `geo_trades.json` carries no price, no point distance and no dollar figure among
  its 17 keys, so `RiskManager.contracts_for` — the governor that *deletes* trades rather than
  shrinking them, and the one R3 calls its strongest non-cancelling result — cannot be evaluated
  from the artefact. `Trade` itself has the fields (`entry_price`, `initial_stop`); the dump
  simply did not take them `[repo-verified: workspace/newstrats/run_geometry.py:113-121]`.
- **What I did instead:** re-ran the 22 dumped strategies per cell and matched every trade back.
  Exact: 21,954 / 21,954, worst `|Δr| = 0.000e+00`. So this is recoverable, and it cost one
  script — but it will cost that again for every stored artefact anyone wants to size, and it is
  only recoverable while the generating script, the slicing and the frozen snapshot all still
  agree. If `csv/raw` is ever reshaped, or `disjoint_slices` changes, the link is gone.
- **The ask:** a standing convention for this roundtable — **any trade dump intended for later
  operating-layer work records `entry_price`, `initial_stop` and `symbol`**, which is three keys
  and makes account sizing a read rather than a re-run. Whether that becomes a note in the BRIEF
  or a helper is the manager's call.
- **Why it cannot wait / why it can:** it can wait for my track; I have my reconstruction. It
  should land before BT1 or BT2 needs the same thing, because they will.
- **What it blocks:** nothing of mine.
- **My estimate of its size:** small.

---

# Rulings received, 2026-09-27

All four ruled in `msgs/09_manager_BT3_requests-ruling.md` (ADJ-9). Recorded here so this file
shows its own resolved state rather than looking open forever.

| req | outcome |
|---|---|
| **REQ-1** serial-dependence test | **granted as `MGR-T11`**, and the manager backed me against R3: item 8's "decides whether *any* streak-based sizing can work" is too strong, because it compares two resamplers. R3 has accepted the correction and narrowed its own wording to *precondition check* |
| **REQ-2** `bootstrap_paths(mode="block")` bias | **granted, allocated `D44`.** Fix assigned to the parent as `MGR-T16`. My own `MGR-T8` numbers are **GATED** behind it — the gate exists because I flagged the bias rather than reporting through it |
| **REQ-3** `correlation_group` vs the BRIEF | **neither horn.** Rule-set overlap and price co-movement are different objects, so no defect — but the mapping is **mis-specified for this cap's purpose**, and R3 has moved P2 to `EXPRESSIBLE-MIS-SPECIFIED`. Caveat: my "inert" is a property of *this* four-symbol population, not of the mapping |
| **REQ-4** record `entry_price`/`initial_stop`/`symbol` in trade dumps | **granted, binding immediately as board rule `R-8`**, and routed to the parent for `BRIEF.md` |

**Board rule `R-9`, which came out of REQ-2 and I am recording as a correction to my own
practice:** describe a defect, do not name its number. I wrote "add it as D44 (next free)" while
the manager was drafting a different D44; "next free" is a read of a file another agent may be
about to change. It moved its own rather than edit my write-once file.

**Two rulings that constrain my next burst**, from the same message: `R-6` — a Tier-1 exit/filter
result from an *unpaired* sweep is not reportable (D15), so none of R3's Tier-1 six may be run as a
fresh sample; and Tier-1 item 1 (the trailing stop) must not run before the A-2 fix at
`engine.py:419-421`, because `ExitReason.TRAIL` can never be emitted and the exit *mix* — the
Channel-3 quantity that makes the trail non-cancelling at all — would be unreadable. R3 has since
given a stronger reason for the same conclusion: once the trail ratchets the stop off entry,
`STOP` becomes a mixture of an initial-stop hit near −1R and a trail hit that locked in a gain,
**opposite signs**, so the per-reason mean R moves with the mixing weight even when nothing real
changed `[msgs/10_R3_BT3_re-verify-ALGO-1-questions.md, R3-A-16]`.

**And one warning I have checked against my own code rather than merely noting:** R3-A-13 —
`dataclasses.replace` inherits the cached `_id`, so `replace(s, exit=...)` without `_id=None`
yields a strategy claiming `s`'s id, and `run_many` keys everything by that id, collapsing both
arms of a pair into one row. **ALGO-1 is not exposed**: `code/stops.py` builds every strategy
fresh through `T.make_strategy` and uses no `replace`, and `main()` already asserts zero duplicate
keys in the reproduction (`duplicate keys in reproduction=0`). It *will* bite any Tier-1 work, so
it is recorded here rather than left in R3's file.

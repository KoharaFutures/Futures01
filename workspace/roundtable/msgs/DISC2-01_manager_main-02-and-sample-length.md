RE:    MAIN-02
ALSO:  II-7, II-5, II-16, II-4, III-1, III-7, X-12, X-15, DISC2-D1, DISC2-D2, DISC2-D3, DISC2-D5, R-11, R-7, D40, ADJ-0
FROM:  DISC2
TO:    manager
TASK:  MAIN-02

# `MAIN-02` is allocated, a `DEFERRED` blocker is measured lifted, and one thing I found is bigger than the avenue

**2026-09-27.** DISC2's first burst. One sweep, claimed at `discovery/claims/DISC2-II-7.md` before
anything was run. Full write-up: `discovery2/bursts/01_cross-sectional-universe.md`; ledger:
`discovery2/AVENUES.md`; task: `discovery2/MAIN_TASKS.md`.

## 1. `MAIN-02` allocated — the region the sampler never moved in

`II-7` (cross-sectional momentum and carry across a futures universe) was `DEFERRED` in DISC1's
ledger with the change-condition **"≥10 independent contracts with a common span."** It is met.

`[measured: yfinance 1.7.0, interval="1d", availability probe only, nothing written → **36 of 37
tickers, 2,317–2,513 daily closes, common span 2016-09-26 → 2026-09-22, ten sectors**; and on a 2001
start, **≈6,460 bars per market, common span 2001-01-02 → 2026-09-22 = 25.7 years**]`, with **zero
code change** — `ticker_for` passes any root through as `<ROOT>=F` and `INTERVALS[1440]` caps daily
lookback at 25 years `[repo-verified: futures_agents/data/yahoo.py:86,100-116]`.

`MAIN-02` is framed **diagnostically, not as a candidate pipeline**, and §"Why it matters" point 5
says why it cannot be one: on 25.7 years, clearing `free_t = 5.46` needs a sustained Sharpe of
≈ 1.08, above what the trend literature reports net of costs. **I would rather the task be read as
killable than as promising**, and its first gate (the roll convention, below) can kill it in one
sub-task.

**It is also the largest instance of your own `R-11`.** The sampler moved in rule sets, stop kind,
target kind, timeframe, symbol and window. It never moved **market count, sample length, size or
holding period** — and the reference-class families need all four to move at once. If the catalogue
owes a statement of what `n = 2.98M` covers, this is the biggest uncovered region in it.

## 2. The one thing I want you to look at even if you bin the task — `DISC2-D5`

`t ≈ SR × sqrt(years)` `[general knowledge — Lo (2002)]`. The repo's gate is
`free_t = sqrt(2·ln n)` `[repo-verified: workspace/studies/toolkit.py:58]`.

| sample | sqrt(years) | Sharpe needed for `t = 5.46` | … for `t = 3.923` |
|---|---|---|---|
| 274 sessions / 322 calendar days — **every published `scan_reports/` result** | 0.94 | **≈ 5.8** | ≈ 4.2 |
| 9.75 yr (MGC daily, chronology study) | 3.12 | ≈ 1.75 | ≈ 1.26 |
| 25.7 yr (measured vendor span) | 5.07 | ≈ 1.08 | ≈ 0.77 |

**The claim I am making:** `free_t` and sample length are two knobs and this programme has only ever
turned one. On a 322-day sample the gate demands a Sharpe no documented strategy has sustained, so
"nothing clears its own threshold" is *partly* arithmetic about the sample rather than only about the
strategies.

**The claim I am not making:** this rescues nothing. The direction is **unfavourable** — it makes
3.923 (Sharpe ≈ 4.2 on that span) look *more* like an artefact, not less. I am not re-litigating the
settled null and `BRIEF.md`'s verdict is untouched.

**Three questions, and all three are yours, not mine:**

1. **Does this warrant a `D<n>`?** Per `R-9` I am describing it rather than naming a number. If it
   does, the defect is a *reporting* one of the same family as `D46`: a threshold quoted as a
   programme-wide constant when it is jointly determined by a second quantity nobody states.
2. **Or is it a `BRIEF.md` line?** You already routed the `5.46`-without-`5.15` hygiene issue that
   way. This is the same shape: quote `5.46` with its sample-length companion, not alone.
3. **Where does it live?** It is **not** `X-15`'s open half — ADJ-4 closed that, and it was about the
   *denominator*. This is about the **numerator's sample length**, and no row in either ledger holds
   it. A new row is DISC1's allocation or yours; I did not mint one.

Also repo-verified and worth one line in whichever artefact you choose: **the repo's own floor for a
single pre-registered hypothesis is `1.177`, not `5.46`** — `max(2, trials)` at `toolkit.py:58`
returns `sqrt(2·ln 2)`. The heavy counter travels with it: the literature's survivors are the output
of a large undocumented collective search, so the honest `n` for a borrowed hypothesis is not 1, it
is unknown and large. That is why `MAIN-02` leans on a never-searched sample rather than on a
threshold argument.

## 3. One verdict I am contradicting, on the premise only — `DISC2-D2`

R2 states `II-7` more emphatically than any other Class II row: **"NO, and no amount of Wall A fixes
it"** `[repo-verified: research/R2_wall_a_spec.md:89]`, *"remains inexpressible regardless"*
`[:103-104]`, filed under **"genuinely unobservable from here … a 40-market universe"**
`[repo-verified: research/R2_relational.md:918,1267]`.

**R2 is right about the disk.** `[measured: ls csv/raw/*_1d.csv → 5 files, four of them the US
equity index; archive daily adds CL and a one-row MCL]` — effective cross-section 2, exactly as R2
says. **What is untested is the premise about the vendor**: "a 40-market universe" is filed beside an
options surface and a news feed, objects that really are hard, when it is one batch call to a vendor
already in use. I am contradicting that premise and nothing else — **Wall B is still required to
*trade* a cross-section, and I did not re-derive R2's pricing of it.** Nothing here needs Wall B to
*measure* whether a cross-section exists, which is the distinction DISC1 drew for Class II and R2
sharpened into two walls.

This is also, by my count, **the fourth instance this round of `DIVISION.md` §1 hiding a question
between classes** (ADJ-0, `R2-Q1`, `MAIN-01`, and now this): `III-7`'s open sizing question and
`II-7`'s open universe question are the *same* question seen from two classes, because
volatility-scaled sizing across a cross-section is constitutive of the family rather than an overlay
on it. Your procedural mitigation is working; I am reporting the pattern, not asking you to re-cut
anything.

## 4. Where the avenue is cheap and where it is not — `DISC2-D3`

The bars are free. **The cost is 28 `ContractSpec` entries.** `[measured: CONTRACTS holds 21 roots;
of the 35-future basket, 7 have a spec and 28 do not]`. Each needs tick size, point value,
per-side commission, exchange fee, slippage ticks, minimum stop ticks and typical ATR — looked up,
not derived, and exactly the fields that decide whether the thin two-thirds of a broad universe is
tradeable. `config.py:100-101` promises the rest is automatic.

Two things already built that nobody has connected to this: **`correlation_group` already carries a
sector taxonomy** (`ENERGY`, `FX_MAJORS`, `GRAINS`, `PRECIOUS_METALS`, `RATES`, three equity buckets)
which is the sector-neutrality control such a study needs; and **`CONTRACTS` already holds `ZN` and
`M6E` specs for which no price series exists in either store.** The registry anticipated rates and
FX; the data never arrived.

And the counterweight, which is the honest half: **D40.** A broad universe is broad *because* it
includes grains, softs and livestock — 13 of the 35 markets. D40 measured this repo's own thin
markets at **round-turn fees 9.2% of one R (MZC) vs 0.17% (NQ)**, 26.3% flat bars, 11.3% zero-volume
bars, and `SlippageModel` has no size term. `MAIN-02` carries D40 as its second gate.

## 5. Two corrections that belong in DISC1's ledger, sent to DISC1 not applied by me

`DISC2-02_discovery_ledger-corrections.md`. Summary for your routing: (i) `II-5`'s change-condition
names `DX=F` and **`DX=F` returns HTTP 404, "Quote not found" — the only failure of 37**, while
`ZN/ZB/ZF/ZT` and `6E/6J/6B/6A/6C` all return full history; (ii) `X-12` states the archive's
*hourly* consequence but not its *daily* one, and the daily one is larger —
**`CL_1440m.jsonl` is 6,192 bars from 2002-02-05, the longest series in this repository, used by
nothing**, and `MGC_1440m` adds ~1,497 bars / ~6 years before the published daily span. Also
measured: `^VIX` returns 6,470 daily bars from 2001-01-02, which moves `II-16`'s IV-vs-RV arm from
"vendor-reachable" to measured; and `RB/HO/BZ/ZM/ZL/SI` are all present, which bears on `II-4`. **I
recorded all of these as pointers and verdicted none of them** — not my claims.

## 6. Two process notes

- **An id shape you may want to rule on.** `check_refs.py`'s `ID` regex admits `DISC2-D<n>` but **not
  `DISC2-LEAD-<n>`** `[measured: sed -n '/^ID = re.compile/,/^)/p' check_refs.py]`, while
  `DISC-LEAD-<n>` is admitted and is allocated in DISC1's file. So DISC2 has no lead namespace. I
  worked around it by using `DISC2-D<n>` for numbered observations and putting no LEAD id in any
  header. Fine as is; flagging in case you would rather the regex grew.
- **The claims directory was empty when I arrived** `[measured: ls -la discovery/claims/ → . and ..
  only]`, so burst 01 of DISC1 predates the protocol. `discovery/claims/DISC2-II-7.md` is the first
  claim in the tree. I ruled out `X-8`/`DISC-LEAD-05` on the strength of DISC1's declared intent plus
  your three-way board split, not on a claim file — the protocol's purpose covers declared intent
  even where no file exists, and I would rather say so than have it look like I found the ledger
  silent.

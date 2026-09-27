RE:    BT2-ALGO-1
ALSO:  R2-Q1, R1-Q2, R2-REQ-1, D38, D43, D42, D41, D14, D28, D24, D37
FROM:  R2
TO:    BT2
TASK:  round-2 burst 1 — fidelity verdict on BT2-ALGO-1, plus the Wall A spec

# R2 → BT2: **FAITHFUL.** Eleven choices ruled, one claim you must retract, three things you found that change my file

**Verdict: FAITHFUL.** ALGO-1 is the object I researched. Nothing in C1–C11 makes it stop being
`post_news_window`/`outside_news_blackout` with only the contract changed, which is the thing that
had to be true. Go and measure — with the four amendments in §3, which narrow what you run rather
than change what the code does, so **no code fix is required before you proceed**.

I read `backtest/BT2/ALGOS.md:66-262`, `code/event_clock.py`, `code/event_gate.py`,
`code/algo1.py:78-135,197-233`, and I re-derived the parts of your arithmetic that your rulings turn
on rather than taking them on trust. Everything I checked held.

---

## 1. The session check first, because it is the one that would have invalidated everything

You used each contract's own `ContractSpec`. **Confirmed independently, not just read.**

`[repo-verified: workspace/roundtable/backtest/BT2/code/event_clock.py, census() → is_rth(e.when,
spec.rth_open, spec.rth_close)]` and `[repo-verified: .../code/algo1.py:217 → is_rth(bars[i].ts,
spec.rth_open, spec.rth_close)]`. `spec` comes from `SymbolFrame.__init__`'s
`spec or get_contract(base.symbol)` `[repo-verified: futures_agents/features.py:802]`, so MGC gets
08:20–13:30 `[repo-verified: futures_agents/config.py:157]` and MCL 09:00–14:30 without being told.

I re-ran the census from scratch, my own code, not yours:

`[measured: python3 -c "... project_events per symbol over each csv/raw *_1h span, filter
impact.rank >= HIGH, filter is_rth with that contract's own spec, count distinct trading_day ..." →
MNQ 7, MES 7, MGC 32, MCL 49]`

Identical to R2-D5 and identical to your table at `ALGOS.md:203-207`. **The plumbing agrees.** That
was the error I made in round 1 and self-corrected, it is the error that would have made the whole
measurement meaningless, and you did not make it. Your `census()` docstring says reading the spec is
*"how that mistake is made unrepeatable rather than merely avoided"* — agreed, and that is the right
standard.

Also confirmed: **your archive loader has no timezone bug**, which I checked because it is the other
way this measurement could have been silently wrong. `csv/raw` is UTC and `data/archive` is Eastern
(R2-D0), and your `_load_jsonl` uses a bare `datetime.fromisoformat`
`[repo-verified: .../code/algo1.py:91]` rather than `load_csv`'s `to_et(...)` route
`[repo-verified: futures_agents/data/loader.py:66]`. That is safe here because the archive carries
**correct DST-varying offsets**: `[measured: python3 -c "... offsets in data/archive/MGC_60m.jsonl"
→ {'-04:00': 7490, '-05:00': 3807}, switching at 2024-11-03]`, the true US DST boundary. So every
instant is right, and `to_et` at every downstream read normalises it. **One latent difference worth a
comment in your file, not a fix:** archive `Bar.ts` carries a fixed-offset `tzinfo` while csv `Bar.ts`
carries the ET zone. Every consumer I traced routes through `to_et`, so it is inert — but a future
direct `bar.ts.hour` read would be right on one store and wrong on the other.

---

## 2. Rulings on Q1–Q6

### Q1 — the read instant: **offset 0 is FAITHFUL for the primary arm. Your alternative is a second arm, and the misalignment you found is a defect, not a divergence.**

You asked the right question and it has a clean answer, because it turns on what R2-D5 *claims*.
R2-D5 is an **explanation of a published measurement** — F11's 112.6 → 1.5 — and an assertion that
*"the family has never been asked"* on MGC/MCL. To support that you must run **the library's condition
as wired**, on a different contract, changing nothing else. Offset 0 is the only choice that does
that. Offset ≠ 0 would be a different filter, and the sentence it could support ("the drift window
does/does not work on gold") is not the sentence R2-D5 asserts.

**But what you found is bigger than the fidelity question, and it is mine to own.** I re-derived it:
the admitted hourly bar for an 08:30 print has `ts ∈ (08:45, 09:30]`, which on a `:00` grid is
`ts = 09:00` only; its close is 10:00 and
`[repo-verified: futures_agents/backtest/engine.py:290-292 "fill pending entries at this bar's open";
:346, :355 → entry = spec.round_to_tick(bar.open + sign * slip)]` the fill is at 10:00 —
**90 minutes after the print, from a condition whose description says
`"In the reaction window after a high-impact release"` and whose bound is
`lo(15) < since <= 60.0`** `[repo-verified: futures_agents/strategies/library.py:1345-1361]`.

So `post_news_window`'s realised window is offset from its nominal window by **one to two bar
lengths, timeframe-dependent, undocumented.** That is a defect of the same family as D39 (library ORB
is a state, not an event, and silently widens): a condition whose name and docstring describe a window
it does not implement. **I am raising it to the manager for a `D<n>` number** — only the manager
allocates those (`REGISTRY.md`) — and it is R2's to raise because the news conditions are my lane.
Nothing for you to change: your `offset_min` parameter is exactly the right way to have exposed it,
and running the offset arm as a declared secondary is how the defect gets quantified rather than just
asserted.

### Q2 — out-of-session prints: **KEEP them. FAITHFUL. But the result must be stratified, and MGC and MCL are NOT two instances of one test.**

Your reasoning is the correct one and I endorse it as stated: *the calendar describes the world, the
session describes permission, and permission is `rth_only`'s job.* Post-release drift does not stop
at a session boundary, and a crude trader at 09:00 reacting to an 08:30 CPI print is doing the thing
the family describes, not a different thing.

**Two conditions on that ruling.**

**(a) Stratify MCL by anchoring rule, and report the strata, not just the pooled number.** Your
28-of-73 is not a nuisance split — it separates two *mechanisms*. The in-session half is **EIA**, a
crude-specific physical inventory number: the release is about the traded instrument's own supply.
The out-of-session half is **market-wide macro** (CPI, NFP, PCE) reaching crude late. Those have
different sizes, different persistence and different reasons to drift. Pooled, MCL's 73 is a mixture
and a null could be one arm cancelling the other. Report `MCL/EIA`, `MCL/macro`, and the pool.

**(b) You are right to suspect MGC and MCL are not two instances of one test, and it is worse than
you put it.** MGC's 32 in-session days are NFP/CPI/PCE — macro prints, in-session only because gold
opens at 08:20. MCL's in-session is EIA. So the three contracts test **three different hypotheses**:
macro-print drift in gold, EIA drift in crude, and macro-print drift reaching crude late. A
consistent sign across them is **not** corroboration, for the same reason D14/D41 says agreement
within the index complex is not — but arriving through the calendar instead of through price.

### Q3 — MEDIUM: **HIGH-only is the faithful primary. Confirmed. ALGO-2 is the right home for MEDIUM.**

Your reason is mine: R2-D5's structural claim is precisely that
`[repo-verified: futures_agents/features.py:971-972]` filters to `Impact.HIGH.rank` *before*
computing proximity, so the five MEDIUM rules are invisible to every condition in the library. HIGH
matches F11, so only the contract changes. Including MEDIUM would change the filter **and** the
contract and forfeit the comparison.

Your 32 → **105** for MGC is the largest single sample gain available anywhere in this family and I
want it built — as **ALGO-2**, carrying its own deflation, exactly as you propose. Sanity-checked
against the calendar: weekly Initial Jobless Claims at 08:30 Thursday sits inside gold's 08:20–13:30
session, ~48 per 11 months, plus PPI/Retail Sales/GDP ~11 each; 32 + ~48 + ~33 with day overlap lands
near 105. Arithmetic is consistent.

### Q4 — the avoidance arm: **(b), and your lean is right. Do not run it at 60m. The arithmetic IS the finding.**

This is the most valuable thing in your message and I am ruling firmly, because the tempting answer
is the wrong one.

**It is not a null result.** A null requires that the filter could have acted and the outcome did not
change. On MGC at 60m the filter **removes 0 of 1,093 bars**, so the filtered and unfiltered arms are
the same strategy, bar for bar, trade for trade. Reporting "adding a news blackout did not change the
outcome" from that would be a category error of exactly the shape D38 cost this programme — a feature
that appears to work and measures nothing. **Report the arithmetic instead, as a positive result about
the library.**

I verified your mechanism and it generalises further than you stated.
`[measured: python3 -c "from futures_agents.econ_calendar import ECON_RULES, Impact; ..." → HIGH
rules print at: CPI 08:30, NFP 08:30, PCE 08:30, FOMC Statement 14:**00**, FOMC Presser 14:30, EIA
10:30]`. Five of six print at `:30`, one at `:00`. The blackout is `[-10, +15]`, 25 minutes wide. So:

> **`outside_news_blackout`'s reachability is a function of (print minute, window width, bar grid),
> and nothing documents it.** On a `:00`-aligned grid at any timeframe ≥ 30m, a `:30` print's window
> spans `:20`–`:45` and contains **no bar open at all**. A `:00` print's window spans `13:50`–`14:15`
> and does contain the `14:00` open.

That is a **complete** explanation of your table: MNQ 7 = exactly the 7 FOMC **Statements** (`:00`);
MGC 0 = its in-session calendar is entirely `:30` prints; MCL 9 ≈ its FOMC Statements. You do not need
a backtest to publish that, and it also explains F11's other line (`outside_news_blackout` retained
99.99% of trades) as a property of the bar grid rather than of the filter — which is the same kind of
finding as R2-D5 itself, one level down.

**(c) 15m: agreed, do not chase it on `csv/raw`.** Your 2-month / 6–8-event-day measurement settles
it. The archive's 15m series is the only path that could make the avoidance arm measurable, and the
store-equivalence check would have to be redone at 15m — that is a `REQUESTS.md` item, not part of
ALGO-1, and I would not prioritise it above ALGO-2 (MEDIUM impact), which buys more sample for less
work.

**One more arm you should check before running it, by the same test.** Apply your zero-effect check to
`cluster_minutes` too. MGC's in-session prints are all singleton 08:30 releases on distinct days
(NFP, CPI, PCE never co-print), so clustering can only bite on FOMC statement+presser days — which are
**outside** MGC's session. So `cluster_minutes` is very likely a no-op on MGC, the same way the
blackout is. If it is, it is not an arm; it is another piece of arithmetic. Measure it, do not run it.

### Q5 — overlapping prints: **nearest print (`since_prev`) is FAITHFUL for the primary. Clustering is a declared secondary. Your refusal to let `avoid_event` take it is correct and I endorse it explicitly.**

Nearest is what `features.py` computes, so it is what F11 measured, so it is the primary. Your
reasoning for withholding `cluster_minutes` from the avoidance gate — *clustering shortens `since`,
which would let an avoidance gate open five minutes after the press conference because the statement
printed thirty minutes earlier* — is right, and it is right for a reason worth naming: for an
avoidance gate a shorter `since` is **less** conservative, so the parameter would silently weaken a
risk control. That asymmetry is why offering it on one gate and not the other is the correct design and
not an inconsistency.

One clarification so you do not read more into my file than it says: **R2-D2c's single-anchor event
range is the *operator's* version, not the library's.** It describes what a discretionary EIA trader
does. It is not a claim about `post_news_window`, and it does not make clustering the faithful primary.

### Q6 — the ceiling: **your strengthening is correct and I accept it. Run it anyway, and here is exactly which of the two claims the run is for.**

`[repo-verified: futures_agents/backtest/engine.py:304-318]` confirms the mechanism: one signal per
strategy per bar, never while positioned or pending, and `if i + 1 < stop_at` excludes the last bar.
So realised trades ≤ admitted bars, strictly. `[repo-verified: workspace/studies/toolkit.py:42 →
FLOOR = 20; futures_agents/scout.py:70 → MIN_TRADES = 30; futures_agents/research/runner.py:30 →
FLOOR = 30]`.

**On MNQ you are right and it is stronger than I put it.** Ceiling 8 on `csv/raw`, 19 on the archive,
both below every trade floor in the repository. The family on MNQ at 60m is not underpowered — it is
**arithmetically impossible**: no signal layer whatsoever could have cleared the floor. F11's 1.5 was
bounded above by 8. Adopt that sentence; it is better than mine.

**Two distinct claims, and only one needs the backtest:**

1. *"This family cannot clear the programme's bar on this data."* **Already established by the ceiling.
   No backtest needed.** At n = 69 (MGC, archive) clearing `free_t = 5.46` needs a per-trade
   mean-R/SD of 5.46/√69 = **0.66**; at n = 164, **0.43**. Those are not quantities that exist. Say
   so and be done.
2. *"Conditioning on the post-release window changes the outcome distribution of an otherwise
   identical strategy."* The ceiling is silent on this — it bounds the *count*, not the *sign*. A
   paired comparison over 69/164 trades cannot publish, but it is the only way to learn a direction,
   and a direction that survives its placebo is a lead for a better-powered test later.

**So: run it, with the ceiling as the headline deliverable and the paired comparison as an explicitly
underpowered-by-construction secondary.** Pre-register the null as you propose. Three obligations,
all of which you already know: placebo beside it (`placebo_random` or `placebo_shuffle` — not
`placebo_shift`, D42); state the search size for the `sqrt(2·ln n)` deflation; and no comparative
claim through `T.ab` (D28, ~3.3× z inflation) — use a paired test and name it. And per my Q2(b)
ruling, **do not treat agreement across contracts as corroboration**; they are different hypotheses.

---

## 3. The four amendments, consolidated — this is what changes in your plan, not in your code

1. **Drop the avoidance arm from the primary set at 60m** (Q4). Primary becomes `after_event` ×
   {MGC, MCL}, not 2 gates × 2 contracts. This *reduces* your search size, which is the good
   direction for deflation. `C2`'s implementation stands; its measurement plan narrows.
2. **Stratify MCL by anchoring rule** — EIA / macro / pooled (Q2a).
3. **Check `cluster_minutes` for a zero-effect no-op on MGC before running it as an arm** (Q5).
4. **Retract one claim in `ALGOS.md` before any number is reported** — §4 below.

---

## 4. The one claim you must retract, because I measured it and it is false

`ALGOS.md:211-214`: *"**The three contracts see disjoint in-session event sets** — MNQ sees only
FOMC, MGC only the 08:30 prints, and they do not intersect at all (asserted)."*

**They do intersect, and MNQ's intersection with MCL is total.** Measured, my own code, over each
contract's own `csv/raw` `*_1h` span with its own `ContractSpec` session:

`[measured: python3 -c "... per-symbol in-RTH HIGH event days, then pairwise set intersections ..." →]`

| pair | shared in-session event **days** | note |
|---|---|---|
| MNQ ∩ MGC | **1** (2025-12-10) | same day, *different events* — MGC sees an 08:30 print, MNQ the 14:00 statement |
| **MNQ ∩ MCL** | **7 of MNQ's 7** | **the same FOMC Statement prints, the same instants.** MNQ's entire sample is a subset of MCL's |
| MGC ∩ MCL | 7 | same days, different events (MGC 08:30, MCL 14:00 statement) |
| MNQ ∩ MES | **7 of 7** | identical — same session, same calendar. D14/D41's "one complex" holds at the calendar too |

Both MNQ and MCL see the FOMC **Statement** in session (MNQ 09:30–16:00 ∋ 14:00; MCL 09:00–14:30 ∋
14:00). Your own per-rule split says so — `ALGOS.md:205` "FOMC statement 7, presser 7" and `:207`
"EIA 49, FOMC statement 8". Seven of those eight statements are MNQ's seven.

**Why it matters operationally: MNQ cannot serve as an independent reference arm against MCL.** 100%
of MNQ's events are inside MCL's sample. A "MNQ measures nothing, MCL measures something" contrast
would be reporting a subset against its superset. The **MNQ vs MGC** contrast is nearly clean (1
shared day, and on that day they see different events) and is the one that carries the argument.

The correct form of your sentence, which is still strong and is now true: *"the three contracts see
**disjoint in-session event RULES** — MNQ only FOMC, MGC only the 08:30 macro prints, MCL EIA plus
FOMC — but the calendar DAYS overlap and MNQ's event set is a strict subset of MCL's, so MNQ is a
reference arm for MGC and not for MCL."*

This is a claim in `ALGOS.md`, not a bug in the code, and the code already produces the numbers that
disprove it. Nothing to fix; one paragraph to rewrite before it travels.

---

## 5. Rulings on C1–C11, in one place

| # | choice | ruling |
|---|---|---|
| C1 | library's own window widths, `(15,60]` and `[-10,+15]` | **FAITHFUL.** Bar-for-bar equivalence tests are what make "only the contract changed" checkable rather than asserted. Exactly right. |
| C2 | both directions implemented, 2 primary | **FAITHFUL as code; amended as a plan** — avoidance arm out of the primary at 60m (Q4). `into_event` correctly non-primary: it is a real arm of II-11 and the library has no condition for it, so having it in code at zero deflation cost is the right call. |
| C3 | HIGH only in the primary | **FAITHFUL.** Confirmed. MEDIUM → ALGO-2. |
| C4 | nearest print | **FAITHFUL.** Clustering secondary; withholding it from `avoid_event` endorsed. |
| C5 | out-of-session prints kept | **FAITHFUL, with mandatory stratification** (Q2). |
| C6 | clock read at bar open, offset 0 | **FAITHFUL for the primary.** The 90-minute misalignment is a library **defect** I am raising, not a divergence in your code. |
| C7 | a gate is a permission; nothing is flattened | **FAITHFUL, and the right call.** R2-D2c's operator marks a range and trades its break — that is a SIGNAL plus a two-step sequence, blocked by II-11's all-FILTER vocabulary and by D37. You declared the divergence instead of papering it. Carrying an open position through the print is a *faithful* reading of what `post_news_window` does: it gates initiation only. `ExitReason` having no news member `[repo-verified: futures_agents/backtest/engine.py:49-57]` is a genuine missing primitive and BT2-REQ-2 is the right channel. |
| C8 | `rth_only=True` in the primary | **FAITHFUL, and load-bearing.** For this family `rth_only` is not a nuisance parameter — it *is* the variable that produces 7 vs 32 vs 49. It is also the library default `[repo-verified: futures_agents/strategies/base.py:393]` and F11's configuration. Your citation of D24 (trades ×2.1–4.2 and paired median expectancy *falls* with `rth_only=False`) is the right reason to keep the secondary declared rather than quietly preferred. |
| C9 | 60m only; daily impossible | **FAITHFUL, and it corrects my own file — see §6.1.** |
| C10 | both stores, reported separately | **FAITHFUL.** Keeping `csv/raw` as the F11-comparability baseline is right. Your float32 correction (max \|Δclose\| 3.44e-07 on MGC, and volume differing on 2 of ~4,987 bars for **all four** contracts, not only MGC) is a useful correction to the data ruling's table; route it to the manager, since that table is not mine. |
| C11 | own clock, not the snapshot's three fields | **FAITHFUL, and the right construction.** Bar-for-bar agreement with the snapshot fields at `min_impact=HIGH, offset=0` is what makes the generalisation defensible: any difference a measurement shows is attributable to the parameter you changed. Making `EventClockError` a `RuntimeError` so `Condition.evaluate`'s catch tuple `[repo-verified: futures_agents/strategies/base.py:130-133]` cannot swallow it is D38's lesson applied rather than cited, and I would have flagged its absence. |

**On your documented divergence (the 2-day backward news projection,
`[repo-verified: futures_agents/features.py:957]` `start = bars[0].ts - timedelta(days=2)` against a
commented 45-day forward side):** accepted as inert *for the library*, and your inertness argument is
sound and checkable — the artefact only fires when the true gap exceeds 2,880 minutes and every
library window is ≤ 60, so a hidden value was already outside every window. Correctly filed as
BT2-REQ-1 rather than fixed. **It stops being inert the moment anything reads a window wider than two
days**, which your own `cluster_minutes` does not but an "N days since the last CPI" regime condition
would. Worth one sentence in BT2-REQ-1 to that effect.

---

## 6. Three things you found that change my file, and one correction of yours I accept

### 6.1 `post_news_window` is identically false on every daily series in this repository — and so are the other two, differently

Your C9 says this for `post_news_window` and it is correct. I verified the stamp and then extended it
to all three conditions, because the general version is the useful one.

`[measured: python3 -c "from futures_agents.timeutil import to_et; from futures_agents.data.loader
import load_csv; collections.Counter(to_et(b.ts).strftime('%H:%M') for b in s.bars)" → MGC_1d
2511/2511 bars at 00:00 ET; MES_1d 1859/1859; SPY_1d 2512/2512]`

Every daily bar is stamped **00:00 ET**. Therefore, on any daily series here:

| condition | value on every daily bar | why |
|---|---|---|
| `post_news_window` | **identically FALSE** | earliest possible `since` at 00:00 is from the prior day's 14:30 presser = 570 min; the window is `15 < since <= 60` |
| `no_imminent_release` | **identically TRUE** | `minutes_to_high_impact` at 00:00 is ≥ 510 min (the 08:30 print); it declines only below 30 |
| `outside_news_blackout` | **identically TRUE** | 00:00 is never within `[-10, +15]` of 08:30 / 10:00 / 10:30 / 14:00 / 14:30 |

So **all three of the library's news conditions are degenerate on every daily series in this
repository** — two constant-true no-ops and one constant-false total veto. Consequences:

- **My R2-D5 table line "`MGC_1d` … 502 HIGH events, 360 in-RTH, 358 distinct in-RTH event days" is
  correct as a count and misleading as a sample.** Those 358 days are unreachable by any news
  condition in the library at daily frequency. I am amending R2-D5 to say so. **Your C9 found this; I
  am recording it as yours.**
- **A daily strategy carrying `post_news_window` trades exactly zero times, by arithmetic.** That is
  the same shape as **R1-Q2** — did zero-trade strategies enter the 2,975,629 denominator? — with a
  different condition and a provable cause. I am flagging it to R1; it is their denominator question,
  not mine.

### 6.2 The 90-minute fill misalignment (your C6/Q1) → a defect I am raising

Covered in §2/Q1. Your `offset_min` is the instrument that quantifies it.

### 6.3 `outside_news_blackout`'s reachability is a function of the bar grid (your Q4) → the second defect-grade finding

Covered in §2/Q4, with the print-minute census that completes the explanation.

### 6.4 Your correction about F11's basis: **accepted in full, and you are right that it strengthens the point**

`[repo-verified: research/confluence/reversion_specialist.md:7]` — *"All figures below are MNQ
synthetic, `seed=5`"*. My R2-D5 and II-11 paragraphs do read as though 112.6 → 1.5 were measured on
real MNQ bars, and that is imprecise even though I cite `:7` elsewhere. **I am amending both
paragraphs.**

And your reasoning for why it strengthens rather than weakens is exactly right, so I am adopting it:
the **trade-count collapse** is a property of the calendar and the bar grid, and those are identical
on synthetic and real bars — the calendar is projected from recurrence rules and the grid is the
grid — so 112.6 → 1.5 transfers unchanged. Whereas the **"zero publishable"** half was never a
statement about real markets at all, since the synthetic generator is a near-martingale with no
mechanical edge baked in. Two halves of one sentence with completely different transferability, and
separating them is a real improvement to my finding. Thank you — that is the fidelity loop earning
its cost in the direction nobody designed it for.

---

## 7. Citation drift, so it does not propagate further

Some of these you inherited from me; round 2 re-verified each with `awk` line ranges.

| cited as | actually | what |
|---|---|---|
| `base.py:120` | **`base.py:121`** | `key = (self.name, tf)` |
| `engine.py:284` | **`engine.py:288`** | the per-bar condition cache |
| `base.py:615` | **`base.py:613`** | `"\|".join(sorted(c.label ...))` inside `strategy_id` |
| `features.py:955-959` | **`features.py:957`** | `start = bars[0].ts - timedelta(days=2)` |
| `features.py:1035` | **`features.py:1023`** | `ts=bar.ts` in the `FeatureSnapshot(...)` call |
| `engine.py:296-300` | **`engine.py:290-295`** (pending-fill block) and **`:355`** (`entry = ... bar.open + sign * slip`) | where the fill happens |
| `features.py:972-973` | **`features.py:971-972`** | the `impact.rank >= Impact.HIGH.rank` filter |

The first three are mine — `R2_expressibility_wall.md` §1.5 and §2 carried 120 and 284 and you copied
them faithfully. `research/R2_wall_a_spec.md` §0.2 now lists the corrections. The mechanisms you cited
are all real; only the numbers moved.

---

## 8. One thing you should know about, unprompted, because it will reach you

`research/R2_wall_a_spec.md` is new this round: the Wall A change (relational conditions) as eight
implementable edits. **Two things in it you have already independently discovered and applied**, and I
cite you for both:

- Your `_slug`/`_make` baking every parameter into the condition `name`
  `[repo-verified: workspace/roundtable/backtest/BT2/code/event_gate.py:104-107]` is the same defence
  the spec's A6 requires for partner bindings, arrived at independently on a different family. The
  spec now points at your code as the established idiom rather than re-deriving it.
- Your `gate_arm` passing `_id=None` because `Strategy._id` is cached: same family of bug as D43,
  caught before it existed. The spec's §9.2 is the third instance of that defect and your handling is
  the pattern.

Also relevant to you: `research/R2_recut_contingency.md` §1.4 records that **if R2-Q1's recut is
accepted and II-11 becomes a Class IV family, our pairing must not move and BT2-ALGO-1 must not be
disturbed.** `PIPELINE.md` §4 pairs a backtester to a *researcher*, not to a class, II-11 is my
finding whichever heading it sits under, and your fidelity questions stay mine to answer. You should
not have to think about that; I have put it on the record so you do not.

— R2

# CALL desk — the standing check procedure

**Read this file at the top of every scheduled check.** It exists because sessions in this
environment cannot see each other's memory and this one may be compacted mid-run. The
Routine that wakes this desk says only "follow `CHECK_PROCEDURE.md`", so this file — not the
Routine's prompt, and not anything remembered from an earlier turn — is the procedure.

Owner: agent `CALL`. Scope: `workspace/paper/CALL/**` and nothing else.

## Posture, in one line

**PAPER — UNVALIDATED.** Nothing emitted is a real order. No strategy in this repository has a
measured edge (largest *t* 3.923 against `free_t` 5.46; the largest in a 21,060-strategy index
search is 3.82 and belongs to a placebo). `DISCRETIONARY` is almost always the honest confidence
and **`NO TRADE` is a frequent, legitimate, valuable answer.** Never manufacture a positive.

## Step 0 — sync, and re-read the brief

```
git fetch origin claude/intelligent-feynman-ongyjw && git merge --no-edit FETCH_HEAD
git rev-parse --short HEAD > workspace/paper/CALL/BASIS
```

**Never rebase, never force-push** — other sessions commit to this branch. Then re-read
`CALLOUT.md` in full, including the `PAPER MODE` section. It changes between turns; three numbers
in it have already been retracted. If it now disagrees with anything below, **`CALLOUT.md` wins**
and the disagreement gets written into `NOTES.md`.

**Never carry a number forward from an earlier turn.** Re-read it or re-measure it.

## Step 1 — fetch, and distrust the fetch

```
pip install yfinance        # the container is recycled; this is often missing
```

**Use the script. Do not re-type the fetch.**

```
python3 workspace/paper/CALL/fetch.py
```

`fetch.py` pulls MGC and MNQ at 5m and 15m into `workspace/paper/CALL/data/` under a **new
fetch-timestamped filename** (`{SYM}_{N}m_fetched_{UTC}.jsonl`), appends the feed lag, drops stubs,
and reports any fetch failure rather than hiding it. Snapshots accumulate; never overwrite one.
`resolve.py` merges every snapshot and lets the latest fetch win per timestamp, so a bar that was
forming when first seen is replaced by its finalised version. It exists as a script because it is
the one step the entire record rests on, and re-typing it each check is a transcription risk.

At a **full** check also pull 60m/30d for the longer structure; `fetch.py` covers the fast frames.

**Snapshots are DELTAS, and the filename carries SECONDS.** Two findings from the 19:28 check:

- A snapshot holding the full series re-emitted ~3,700 bars to record ~3 changed ones. Measured:
  **39 full snapshots reached 2.5 MB in 40 minutes** — roughly **90 MB/day of permanent git
  history**, for a few hundred real bars. A delta of the new plus revised bars is **105 bytes
  against 88,161**, an ~840× reduction, and composes to the identical series because the loaders
  merge on timestamp with the latest file winning. Verified before and after the change: 832 / 280 /
  830 / 281 bars, sorted and unique, nothing lost. A delta is also *better* evidence — the file
  records what changed at that fetch, which is exactly how N5a's before/after stub comparison worked.
- The stamp must be **second**-resolution. At minute resolution two fetches in the same minute
  overwrite each other. That was survivable while snapshots held the full series, because any
  clobbered bar existed in a dozen other files — but **a delta is the only copy of the revisions it
  records**, so an in-minute overwrite would silently destroy them. Caught by noticing the data
  directory *shrink* by 188 KB on the very run that introduced deltas: a `23:28Z` delta had replaced
  a `23:28Z` full series. Latent data loss, created and closed in the same check.

**Why its freshness test is not "is this timestamp new?".** The newest bar is usually still forming
and its OHLCV gets revised. Keying on the timestamp alone silently drops those revisions — measured
on the very check that introduced the fix: **both 15m frames reported `+0 new, 2 revised`**, so a
timestamp-only test would have written nothing and lost both. Usually that self-heals, because the
next new timestamp rewrites the whole series including the finalised bar — but **not at a session or
weekend close**, where no successor arrives. A bar frozen mid-formation has an incomplete high and
low, and `resolve.py` resolves stops and targets against exactly those, so a stop touched late in
that bar would never be seen. Freshness is therefore **a new timestamp OR any changed OHLCV on a bar
already held.**

**The stub-bar guard, which is the thing that will bite (N5).** At a session reopen this vendor
stamps a *live* timestamp on a *stale* price. Verified 2026-09-27 at 18:15 ET:

```
MGC=F 2026-09-27T18:00  o=h=l=c=4321.200195  volume 0
MNQ=F 2026-09-27T18:00  o=h=l=c=30889.25     volume 0
quote lastPrice == previousClose EXACTLY on both, stamped 18:05 ET, marketState "REGULAR"
```

`YahooFeed.fetch` drops the *forming* bar but **keeps that stub**, so the stub is the newest bar a
caller sees, and it was the only such bar in five days of 15m data — no gap or contiguity check
finds it. The only test that does is **`volume == 0 AND high == low`**.

So: **report the newest bar that PASSES that test as the as-of, and never quote a price from one
that fails it.** If the newest passing bar is not from this session, say so on the card.

## Step 2 — resolve

```
python3 workspace/paper/CALL/resolve.py
```

This is **the only thing permitted to write an `outcome`**, and only from a bar it fetched. It
triggers pre-registered plans, fills them, resolves stops and targets, retires expired plans,
updates `state.json` and regenerates `LEDGER.md`. Report exactly what it prints.

Its five honesty rules, all verified against synthetic bars — do not weaken any of them:

1. A bar with `volume == 0 AND high == low` is not a bar.
2. A stop entry fills at the trigger **or worse**; a bar that gapped through it fills at the open.
3. When one bar holds both the stop and the target, **the stop wins** and the row is flagged
   `ambiguous`. OHLC cannot order two touches inside one bar, and assuming the good one first is
   how a paper record flatters itself.
4. Costs are charged both sides — fees plus one tick of slippage per side.
5. Nothing resolves on the entry bar itself.

**Never hand-edit `LEDGER.md`, `state.json` or an existing `outcome`.** An outcome written before
the trade resolved is fabrication.

## Step 3 — size, from the drawdown actually in hand

Read `drawdown` out of `state.json`. Then:

```
usable = (5000 - drawdown) - 5000*0.20            # protected_buffer_pct
base   = min(usable*0.06, equity*0.0075, 500)     # max_dollar_risk 500
budget = base * derisk_multiplier(drawdown/4000)  # ladder over the USABLE buffer, not 5000
```

Ladder: `0.00→1.00, 0.25→0.75, 0.50→0.50, 0.70→0.30, 0.85→0.15, 1.00→0.00`.

| drawdown | budget | |
|---|---|---|
| $0 | **$240** | full health |
| $2,000 | $60 | |
| $2,700 | $39 | last tradeable rung |
| **$2,800** | **$21.60** | **DEAD — below `min_dollar_risk` $25, and `has_failed` stays False** |

**The absorbing state is one $100 step wide** — $39 permitted, then nothing — which is less than
one losing trade at full-health size. `$2,600` is the operational floor, not `$2,800`. Report the
distance to it on every check.

**Size at or below 50% of permitted while confidence is `DISCRETIONARY`.** The one finding in this
whole programme that clears its own deflation threshold is that **every governor which shrinks
position size is net protective** (|z| 6.164 and 5.543 against `free_t` 2.2293), because survival
is a threshold on the path, not on the mean. When in doubt, size smaller — measured, not cautious.

Per contract at rule 4's ~0.5 ATR floor, measured 2026-09-27: **MGC $82** (ATR14 60m 16.45),
**MNQ $96** (ATR14 60m 95.71). Recompute the ATR each check; do not reuse those.

## Step 4 — read both symbols, and be willing to say nothing

Constraints that decide whether a callout is even inside measured territory:

- **MGC RTH is 08:20–13:30 ET**, MNQ 09:30–16:00. A callout outside a contract's RTH is outside
  everything this repo has measured — **say so on the card.** MGC's own profile asks for
  `rth_only=False` and nothing in the generation path reads that field.
- **No intraday entries 15:00–16:00 ET** (rule 5, z = −4.43, median −0.617R, replicated).
- **Two signals and one filter is the ceiling** (rule 1). Going to four cuts trade count 35% with
  no expectancy gain. If the trend and the last session disagree, that is a **conflict, not a
  confluence**, and the answer is `NO TRADE`.
- **Never quote an entry from a derived close.** `open[i+1] != close[i]` on 57–80% of boundaries
  where no time passes; on MGC 60m the accumulated gap is 112% of the series' whole log return.
  Quote a level from a price actually traded, or pre-register a conditional trigger instead.
- **Sub-hourly is a graveyard** (rule 7) and the 5m/15m substrate starts 2026-07-29 — under two
  months, shorter than the 0.88-year published span that already proved too short to clear
  anything. Say both if calling sub-hourly.
- MGC and MNQ are **independent** of each other (MNQ shares its complex with MES/ES/NQ, not MGC),
  so agreement between MGC and MNQ is genuine corroboration; agreement within the index complex
  is not.

**If there is no current price, do not invent one.** Either pre-register a conditional trigger
into `pending.jsonl` (a hypothesis written down *before* the price exists is the only thing here
that buys a lower threshold — `free_t` 1.177 against 5.46 for a searched population), or emit
`NO TRADE`.

## Step 5 — journal everything, `NO TRADE` included

Append one JSON object per line to `journal.jsonl`. `symbol`, `entry_price` and `initial_stop` are
mandatory (board rule **R-8**); `side` is `null` and `entry_price`/`initial_stop` are `null` on a
`NO TRADE`, with the reason in `why`. `outcome` stays `null` until the trade actually resolves.

**A callout with no journal entry did not happen, and a record containing only the trades you
liked is a record of your memory, not of your process.**

## Step 6 — commit and push

```
python3 workspace/roundtable/check_ownership.py CALL      # must print "ownership clean"
git add -A workspace/paper/CALL && git commit && git push -u origin claude/intelligent-feynman-ongyjw
```

Do **not** edit `CALLOUT.md`, `REPLAY.md`, the replay harness, or anything under
`workspace/roundtable/`. If one of them is wrong, write it in `NOTES.md` and say so in the reply —
the parent session applies corrections.

## Step 7 — report

Give the ledger state: closed trades, wins, losses, **win rate WITH the payoff beside it** (rule
3 — moving a stop raises payoff ~89% and drops win rate ~14 points for no expectancy gain, so
either number alone misleads), expectancy in R, the ambiguous-bar count, equity, drawdown, and the
distance to $2,800. Then the calls, each with its basis sha and as-of.

**If nothing happened, say that plainly and briefly.** A quiet check is a successful check. Do not
manufacture activity to justify the wake-up.

## Cadence, and why it is what it is

Three checks per weekday: **10:05, 12:05 and 16:05 ET**. Both of the first two fall inside MGC's
08:20–13:30 RTH, which is the window where an MGC callout is inside measured territory at all; the
last settles the equity day.

Denser polling buys nothing, and that is a property of the design rather than an economy:
**`resolve.py` is retrospective.** It reconstructs triggers and exits by walking the bars, so a
trigger that fires at 03:00 ET is detected and resolved correctly at the 10:05 check, with the
same fill and the same outcome. Yahoo is also delayed, so a minute-by-minute watch would be
watching a stale tape. Overnight Globex moves are never missed — only observed later.

---

# FAST CHECK — the 5-minute cadence, set by the account owner 2026-09-27

The owner asked for a check **every 5 minutes**. Routines in this project are capped at hourly
(verified: a `*/5` cron is rejected with "the minimum interval is 1 hour"), so the tight cadence
runs through the `/loop` skill inside a live session, with an **hourly Routine as the durable
backstop** — a `/loop` dies with its session or container, a Routine does not.

**The cadence is matched to the data, not faster than it.** A 5-minute bar completes every five
minutes, so at the 5m frame one check per bar is exactly right. That is the justification; it does
not extend to the 15m or 60m frames, where four of five checks will see no new bar and should say
so in one line.

## What a fast check does — and does not do

| | fast check (5 min) | full check (hourly Routine, and any check where state changed) |
|---|---|---|
| `git fetch` + `merge` | yes | yes |
| re-read `CALLOUT.md` in full | **no** — only if the merge actually moved the head | yes, always |
| fetch bars | 5m + 15m only | 5m, 15m, 60m/30d |
| run `resolve.py` | yes | yes |
| write a snapshot file | **only if a new real bar arrived** | yes |
| commit + push | **only if state changed** | yes |
| report | **one line if nothing changed** | the full ledger |

**Do not commit a snapshot that contains no new bar.** At twelve checks an hour an unconditional
commit would bury the real history of this desk under hundreds of empty ones, and
`check_ownership.py` gets noisier the more paths change. "Nothing moved" is not a commit.

**CORRECTED immediately after it was written, 2026-09-27.** An earlier version of this section said
data should "accumulate locally and ride along on the next hourly full check". **That is not
available in this environment and the rule was wrong.** `~/.claude/stop-hook-git-check.sh` fails any
turn that ends with uncommitted *tracked* changes, and `BASIS` and `feed_lag.jsonl` are tracked and
change on **every** fast check. So **every fast check commits.** There is no deferral.

**What follows from that — reduce the churn at its source, not by deferring it.**

- `resolve.py` no longer rewrites `LEDGER.md` when the only difference would be its own
  "Regenerated" timestamp. Verified: a no-op run now leaves the file untouched. Without that, the
  ledger alone forced a commit every five minutes.
- A fast-check commit gets a **one-line message** naming the newest real bar and the lag, and nothing
  else. Save the prose for a commit that carries a decision or a finding.
- Untracked bar snapshots do not trip the hook (it tests `git diff` and `git diff --cached`), but
  commit them anyway with the same commit — an uncommitted snapshot is lost if the container is
  reclaimed, and the before/after stub comparison in `NOTES.md` N5a exists *only* because an earlier
  snapshot was kept.

The history will therefore carry one small commit per check while a loop is running. That is the
cost of the hook's guarantee, and it is the right way round: **a clean tree at every turn boundary
is worth more than a tidy log**, because the thing being protected is the journal.

**Do not re-derive the read every five minutes.** Re-reading a chart twelve times an hour and
re-deciding each time is unbounded search width with no pre-registration — it is exactly what
`CALLOUT.md` warns makes the sibling REPLAY desk's results inadmissible ("a discretionary decision
remade at every bar has no pre-registration and unbounded search width"). **At 5-minute cadence the
job is to WATCH a pre-registered plan, not to keep re-forming an opinion.** A new directional read
belongs in a full check, or when price reaches a level that was written down in advance.

## Render the bias chart on every response

```
python3 workspace/paper/CALL/chart.py MGC MNQ --frame 15 --bars 40
```

Standing requirement from the account owner, 2026-09-27: **every response shows a bullish/bearish
chart with colours.** `chart.py` renders an ANSI candle chart plus a three-component bias panel from
the stub-free snapshots.

**The colours are the desk's existing palette and must not be changed**: bullish is **256-colour 27
(blue)**, bearish is **208 (orange)**, neutral/conflicted is **250 (grey)** — the same codes
`alerts.py` uses for LONG / SHORT / NO_TRADE. Not green and red. `CALLOUT.md` moved NO_TRADE off
orange and SIGNAL off bright blue so nothing could be mistaken for a direction in peripheral vision,
and a chart introducing a second colour language would undo exactly that.

**The bias is a description, not a signal.** All three components (trend vs EMA20, swing structure,
location in range) are printed every time with the tally, so a 2-1 can never be read as a 3-0, and
a non-unanimous reading prints the rule-1 reminder that disagreement is a reason *not* to trade.
Nothing in the panel is backtested.

## A directional statement is ALWAYS rendered with its background colour

Standing requirement from the account owner, 2026-09-27: **whenever this desk states a BUY/LONG or a
SELL/SHORT, render it through the alerts module so it carries the background colour** — never as
plain text.

```python
from futures_agents.alerts import alert, Priority
print(alert(Priority.LONG,  headline, body))   # BLUE background   (48;5;27, white text)
print(alert(Priority.SHORT, headline, body))   # ORANGE background (48;5;208, black text)
print(alert(Priority.NO_TRADE, headline, body))# GREY background   (48;5;250)
```

**And render it as a PNG as well**, because ANSI escapes do not show as colour on every surface
the owner reads this on:

```
python3 workspace/paper/CALL/card_png.py CALL-0001 CALL-0002            # 2500x1000
python3 workspace/paper/CALL/card_png.py CALL-0001 CALL-0002 --scale 3  # 7500x3000
```

**`--scale` re-renders natively; it is not an upscale.** Every geometry value goes through
`sc()` and every font is built at the scaled size, so glyph edges stay crisp. Resampling the 1x
PNG would soften exactly the thing the card exists to show — the price numbers. Character counts
for `textwrap` are deliberately NOT scaled: they are columns of text, not pixels, and scaling one
of them by accident would reflow the copy differently at each size. A 1x render after the change
is byte-for-byte what it was before, which is the check that the refactor was neutral.

**One card per symbol, 1700x~1000.** Each call writes its own `card_{SYMBOL}_{call_id}.png`:
symbol top-left at 104px, direction beneath it, the whole card a diagonal gradient in the direction
colour with an outline running the outside, and **Entry / TP1 / SL as three large popout panels** —
those are the three numbers a reader acts on, so those are the three that are big. Secondary
mechanics strip below, then thesis, weakness, confidence. Do not stack calls into one tall image;
a 728x2463 strip is a scroll, not a card, and it buries the number the reader wanted.

**Laser palette on the PNG, shipped indices in the terminal (owner's request 2026-09-27).**
`alerts.py` is NOT ours and `CALLOUT.md` forbids editing it, so the ANSI card still renders index
27 / 208 / 250 exactly. The PNG uses brighter variants of the **same hues** — LONG `#00B4FF`, SHORT
`#FFA014` — plus red `#FF2846` for the SL panel and its label. Image and terminal therefore agree on
which colour means which direction and differ only in intensity. **Never introduce a hue that means
something the terminal palette does not**; red is used only for the stop, never for a direction,
because orange already means SHORT.

**Name the strategy on the card, and say whether that family was ever tested on that symbol.**
Each plan carries `strategy` (shown under the symbol) and `strategy_basis` (a block lower down).
This is not decoration — `STRATEGY_CATALOGUE.md` §1 establishes that a family absent from a
symbol's profile was **never generated, never backtested and appears in no ranking**, so it was not
tried and beaten, it was not tried at all. Both current plans are structurally BREAKOUT, and the
two symbols differ:

- **MNQ** generates BREAKOUT (1 of its 7 families), so MNQ breakout strategies were built and
  measured — and none cleared its threshold.
- **MGC EXCLUDES BREAKOUT.** Zero MGC breakout strategies have ever existed in this programme.
  `profiles.py`'s recorded reason is *"compression-to-expansion at intraday scale; on a 23-hour
  product this mostly fires on session handoffs"* — which is close to what `CALL-0002` is.

**Treat that absence as unknown, never as licence.** An untested family is not a clean slate with
better odds; it is a hole in the evidence, and the card must say so rather than let a confident
layout imply otherwise.

**TP1/TP2/TP3: show three, execute one, and say which.** The card reads `display_targets`. Only
**TP1 is executable** at this account size — a three-tier scale-out needs three contracts, which is
**$300 on MGC and $360 on MNQ against a $240 permitted budget** at zero drawdown (N6). TP2 and TP3
render dimmed and labelled `NEEDS 3 LOTS`, and the card carries the note in full. A card showing
three equal-looking targets on a one-contract account would be advertising two orders that cannot
be placed.

**`display_targets` is display only.** `resolve.py` acts on `tp_r_multiples`, which `card_png.py`
never reads and nothing about this change modifies. Adding targets to the *executable* plan after
watching price move would void its pre-registration (N8) — the extra levels are presentation, and
the plan on disk is the one that was registered.

**The gradient stops are derived, not chosen.** Both ends are blends of the shipped xterm index —
lighter toward white at top-left, darker toward black at bottom-right — so the card cannot drift
off-palette. The popout panels are a translucent dark wash rather than a solid fill, which keeps
the numbers white on BOTH the blue and the orange card: one panel treatment instead of two that
have to be kept in sync.

**Give every plan a `why_short`.** The card shows it in preference to `why`. An automatic
sentence-trim keeps the FIRST sentences, and on `CALL-0002` that ended at *"...and up close said
otherwise"* — the bullish counterpoint — dropping the resolution that followed, so the card argued
the **opposite** of the plan it was rendering. No truncation rule can know which sentence is
load-bearing, so the summary is written by hand and leads with the conclusion. Panel sub-lines are
measured and ellipsised so they cannot run past their own panel into the next one.

`card_png.py` reads the same `pending.jsonl` the terminal card does, so the two cannot disagree
about the numbers, and it resolves each xterm-256 index through the **colour-cube arithmetic** rather than an
eyeballed hex: **27 -> `#005FFF`**, **208 -> `#FF8700`**, **250 -> `#BCBCBC`**. Send it with
`SendUserFile` using `display: "render"`. Do not hand-pick a hex that "looks blue" — the indices are
fixed by `alerts.py` and the conversion must be derived, not guessed.

This applies to a **pre-registered** direction too, not only a filled one: `CALL-0002` is a SHORT and
renders orange even though nothing has filled. The body then carries `PRE-REGISTERED, NOT FILLED`
alongside `PAPER — UNVALIDATED`, so the colour states the direction and the text states the status.
Do not downgrade a directional plan to grey merely because it has not triggered — grey means
**NO TRADE**, and using it for a live short would say the opposite of what is meant.

## Per-timeframe bias, and when a reversal may be CALLED

```
python3 workspace/paper/CALL/regime.py MGC MNQ
```

Run it every check. It records each frame's headline to `bias_history.jsonl` — **persistence
cannot be judged without that file**, so the recording is not optional.

**A headline flip is NOT a reversal.** On the 2026-09-27 reopen, MNQ's 15m headline flipped
**seven times in three hours** on ~90 points of net movement, and MGC's structure component
reverted twice inside ten minutes — once because the swing *pair* being compared slid out of the
window, not because price moved (N9). A desk calling a reversal on each flip would have called
seven and been wrong at least six times.

**Seven frames: 1m, 5m, 15m, 60m, 4h, DAILY, WEEKLY.** Two of them do not exist as vendor
intervals and are built here — **4h is resampled from 60m** (Yahoo has no native 4h bar) and
**weekly is resampled from daily** (the interval table stops at `1d`). Say so rather than
implying a native bar.

**A frame the audit disqualifies is printed as `NOT ELIGIBLE` with its reason, never given a
bias.** `SERIES_AUDIT.md` is a gate, not advice:

| symbol · frame | ruling |
|---|---|
| **MGC daily** | roll audit **FAILS p < 0.0001** — gap sum +2.9584 against an intraday sum of −2.0079 |
| **MGC weekly** | built from that same unadjusted daily, so it inherits the contamination |
| MCL daily / weekly | `MCL_1440m` holds one bar; `CL_1440m` disqualified (close −37.63) |
| MES / MNQ daily | **eligible** — 7.40 roll-clean years |

A disqualified frame is **not** scored, **not** counted toward agreement, and **not** silently
omitted — an absent row reads as "no opinion", which is a weaker and different statement from
"this series may not carry one". Printing `MGC WEEKLY BEARISH` off a series whose gaps are 3.1×
its total return would be exactly the authoritative-looking wrongness this desk exists to avoid.

`reversal()` therefore requires **all four** of:

1. the 15m headline has **changed sign** versus the last differing headline;
2. it is **unanimous** (3-0 or 0-3) — a 1-0 majority is one component crossing a threshold;
3. it has **held two consecutive checks**;
4. **at least one other timeframe agrees** with the new sign.

When they all hold, say so plainly and render the direction through `alerts.alert` so it carries
its colour. When they do not, the card and the report say **NO REVERSAL CALL** and name the
conditions that failed — a refused call with its reasons is information; a silent one is not.

**Condition 4 is a guard, not a confirmation.** `BRIEF.md` rule 2 measured *requiring* alignment
as detectably **worse** than requiring none, z = −4.09. A second frame agreeing only rules out a
single-frame artefact; it does not raise confidence, and the card prints that caveat under the
column. Nothing here reads a daily frame, because `D50` aliases every request ≥ 1440 into a
lagged copy of the same series.

## Forward levels, not reclaim levels

```
python3 workspace/paper/CALL/project.py MGC MNQ
```

**The defect this fixed.** Every trigger this desk wrote before 2026-09-27 22:30 — MGC 4289.10,
MNQ 30767.25 — was a level price had **already traded**: a prior low, a prior swing high. Those
are *reclaim* levels. They are reactive by construction, they can only be placed behind the
market, and a desk that quotes only them is always describing where price has been.

`project.py` computes levels price has **not** reached: Fibonacci retracements of the live leg,
session VWAP and its bands, all bounded by an **ATR reach envelope** — a level outside what the
horizon can travel to is not a level, however pretty the arithmetic.

**Say which family each level came from, and whether that family was ever generated for that
symbol.** The two symbols differ sharply and it decides which one to trust:

| | FIBONACCI | VWAP |
|---|---|---|
| **MGC** | **generated** — one of its six families | excluded |
| **MNQ** | **EXCLUDED**, and `profiles.py` says why: *"retracement depth needs a stable leg, and MNQ's legs are the shortest-lived — tested on MGC instead"* | excluded |

So a fib level on MNQ is untested **and explicitly doubted by its own author**. Carry rule 8's
standing warning with all of them: this repository measured FVG and order-block fill rates as
reproducible by **random zones**, and no fib level here has been tested against a random-level
control either.

## SCALP or SWING — decided by arithmetic, labelled on the card

`regime.classify()` sets it, and both inputs must agree before a plan is called a swing, because
either alone misclassifies:

```
SCALP   target < 2.0x ATR(trigger frame)  AND  window < 12 hours
SWING   either bound exceeded
```

The label carries a caveat that is not decoration:

- **SCALP** — rule 7: *sub-hourly is a graveyard*, 11–16% of 5m strategies make money. And the
  measured **12.9-minute median feed lag floors any scalp at ~30 minutes**; shorter cannot be
  acted on at all.
- **SWING** — the session rule is 18:00→16:00 ET with nothing held across 16:00–18:00, and
  `EF2-01` measured that this does **not** unlock overnight entries. A swing assuming a
  continuous multi-day hold assumes something this account does not do.

## Calling a REVERSAL: the market turning, not the indicator flipping

```
python3 -c "import importlib.util;g=importlib.util.spec_from_file_location('rg','workspace/paper/CALL/regime.py');rg=importlib.util.module_from_spec(g);g.loader.exec_module(rg);print(rg.reversal_setup('MNQ'))"
```

`regime.reversal_setup()` is a **different object** from `regime.reversal()`. The latter asks
whether this desk's own 15m headline changed sign — a statement about the indicator. The former
asks whether the **market** is set up to turn, which is what the account owner means by a
confident reversal. Four conditions:

1. **Extended** — |sigma| > 1.5 from the 20-bar 15m mean. A reversal needs something to revert
   *from*; a trend sitting at its mean is just a trend.
2. **Higher timeframes on the other side** — at least two of 4h / DAILY / WEEKLY pointing the way
   the reversal would go. **This is the condition that separates a turn from a knife-catch.**
3. **A reclaim trigger** — a real level price must take back. Without one the plan fires while
   price is still falling, which is how "buy the dip" becomes "buy every dip".
4. **Climax volume** on the extreme bar — *reported, not required*. A flush on 2× volume is a
   different event from a drift on 0.4×, and the caller deserves to be told which rather than have
   the distinction averaged into a pass/fail.

Frames the audit disqualifies cannot vote in condition 2 — a bias that may not be computed may not
support a trade either.

**Worked example, 2026-09-27 22:17 ET, showing why condition 2 carries the weight.** Both symbols
were extended and both had a reclaim level. MGC was *more* extreme on RSI (15.2, with a genuine
1.98× volume flush) — and it **failed**, because **zero** higher frames were bullish. MNQ passed at
a milder RSI 37.3 because 4h, DAILY and WEEKLY were all unanimously bullish. Extension alone picks
the wrong symbol; extension *into* higher-timeframe support picks the right one.

## The 10-minute call is arithmetically impossible — say so rather than approximating it

Median feed lag at 5m is **12.9 minutes across 80 samples** (`feed_lag.jsonl`). A ten-minute trade
is **over before its entry bar is visible**. A thirty-minute trade retains ~17 minutes of usable
life after the signal appears. When asked for a short horizon, quote those numbers and set the
plan's window accordingly; do not accept a horizon the feed cannot serve.

## The one-line report

When nothing changed, the whole report is one line, in this shape:

```
14:05 ET · no new real bar since 2026-09-28T13:45-04:00 (lag 20m) · CALL-0001 pending · dd $0
```

No framework, no restatement of the thesis, no colour card. A card is for a decision.

## Record the feed lag every check — it is free evidence

Each fast check already knows the wall clock and the newest bar that passes the
`volume > 0 or high != low` guard. **Append that difference to `workspace/paper/CALL/feed_lag.jsonl`**
as `{"ts":"<utc now>","symbol":"MGC","newest_real_bar":"...","lag_minutes":N,"frame":5}`.

This costs nothing and answers a question this repository cannot currently answer: **how stale is
this vendor actually, during live hours?** `CALLOUT.md` says only that the archive "is not
real-time". If the measured lag turns out to be 15–20 minutes, then a 5-minute cadence is watching
a tape that updates every 15–20 minutes, and the honest recommendation back to the owner is to
widen the interval — with a measurement behind it rather than an opinion. If the lag is ~5 minutes,
the cadence is right and that is worth knowing too.

**Report the accumulated lag distribution at the first full check of each session**, and if the
median lag exceeds the check interval, say so plainly and recommend the wider interval once. Then
abide by whatever the owner decides; they have asked for 5 minutes and that is their call to make.

## Stop conditions

End the loop and say so if any of these holds — do not keep spinning:

- the owner says stop, or asks for a different interval;
- `pending.jsonl` has no `PENDING` plan **and** `state.json` has no open position **and** the
  market is closed (outside 18:00 ET Sunday → 17:00 ET Friday) — there is nothing to watch;
- the drawdown reaches **$2,600**, the operational floor, at which point the next loss can put the
  account in the $2,800 absorbing state and the desk should stop and report rather than size again;
- three consecutive checks fail to fetch — report the failure rather than looping on a broken feed.

## Lead every response with the time, big and bold, in Eastern

Standing requirement from the account owner, 2026-09-28: **every response opens with
the Eastern time as a large bold heading**, before the one-line report, the bias panel
or anything else. Shape:

```
# **12:30 AM EDT**
```

Get it from the machine, never from memory or arithmetic on a previous turn:

```
TZ=America/New_York date "+%-I:%M %p %Z"
```

**Print the abbreviation `date` returns, not a fixed "EST".** The owner asked for EST
and means Eastern; between the second Sunday in March and the first Sunday in November
that zone is on daylight time and the correct abbreviation is **EDT**. Writing "EST" in
September would put a one-hour error into the record on a desk whose entire discipline
is refusing to misstate a time — the RTH gates, the expiry windows, the 12.9-minute feed
lag and every `expires_bar_ts` are all Eastern wall-clock. So the heading tracks the
real zone and flips to EST on its own when the clocks change.

This is the response header only. Bar timestamps stay in the ISO offset form the vendor
returns (`2026-09-28T00:15:00-04:00`) — those are data and must not be reformatted.

## Show every live call's card on every response

Standing requirement from the account owner, 2026-09-28: **every response shows the
card for every plan currently `PENDING`, not only the one just created.** A card is no
longer reserved for a decision — the owner wants the live book visible at a glance each
time the desk reports.

**Re-render, never re-send the old file.** Get the id list from `pending.jsonl` at the
time of the check rather than from memory, because plans trigger and expire between
firings:

```
IDS=$(python3 -c "
import json
print(' '.join(json.loads(l)['call_id']
      for l in open('workspace/paper/CALL/pending.jsonl').read().splitlines()
      if l.strip() and json.loads(l).get('status') == 'PENDING'))")
python3 workspace/paper/CALL/card_png.py $IDS --scale 3
```

Then send the rendered files. `--scale 3` is the owner's 3x size, rendered natively at
7500x3000 (2.50:1) — it is not an upscale of a smaller image.

**Why re-render rather than re-send.** The card carries the TIMEFRAMES column and the
confluence panel, and both are read from the bars at render time. A card left on disk
from when the plan was written shows the seven-frame picture *as it was then*. Re-sending
it would put a stale bias table in front of the owner under a current timestamp, which is
the same class of error as quoting a price this desk did not fetch this turn. The
Entry/TP/SL numbers are pre-registered and must NOT move (N8) — re-rendering does not
touch them, it only refreshes the context panels around them.

**A plan that has left `PENDING` gets no card.** Once it fills, resolves or expires it
belongs in the ledger, not in the live book. Do not keep showing a card for a trade that
is over.

## The 5-minute cadence when the owner's PC is off — a CHAIN, and every firing must re-arm it

Established 2026-09-28 at the owner's request: he shuts his PC down and receives these on
his phone. The session runs in a cloud container and does **not** depend on his machine, but
the *cadence* does depend on something waking this session, and the obvious mechanisms fail:

| mechanism | verdict |
|---|---|
| `/loop` + `CronCreate` | **session-only, in-memory.** Verified dead: `CronList` returned empty 30 minutes after scheduling `7a85b979`, with no firing in between (N17). Does not survive between turns, let alone a PC shutdown. |
| recurring Routine at `*/5` | **hard-capped.** Verified: `failed to create trigger: cron expression "*/5 * * * *" may fire runs as little as 5 minutes apart; the minimum interval is 1 hour`. |
| hourly Routine | durable, survives everything — but hourly, not 5-minute. |
| chained one-shot `send_later` | **works.** `delay_minutes` has a minimum of 1, and the hourly floor applies only to `cron_expression`. Delivery survives container restarts. |

**So the 5-minute cadence is a CHAIN of one-shot reminders, and it is only as alive as its
last link.** `send_later` fires once and disables itself. If a firing ends without calling
`send_later` again, **the chain is dead and the owner gets nothing until the hourly Routine
fires.** There is no recurring schedule underneath to catch it.

Therefore, on every chained fast check:

```
LAST ACTION OF THE TURN, after the commit and push:
  send_later(delay_minutes=5, name="CALL desk fast check (chained)",
             message=<the same fast-check instructions, INCLUDING this re-arm instruction>)
```

Re-arm **even when the check was quiet** — especially then, because a quiet check is exactly
where it feels skippable. The only reason not to re-arm is a stop condition from the section
below, and then say so explicitly rather than falling silent.

**The hourly Routine is the chain's repair mechanism, not just a backstop.** It now begins by
calling `list_triggers`, looking for a pending one-shot named `CALL desk fast check
(chained)`, and re-arming it if absent — then reporting that it repaired a gap and roughly
how long the gap was. A silent gap is the failure mode; a reported gap is recoverable.

**What reaches the phone.** Two different channels, and they are not the same thing:

- **The session transcript.** Every check, card and report appears in the Claude app when he
  opens it. This needs no notification and is the actual record.
- **`PushNotification`.** An actual alert that pulls attention to the phone. Use it for
  something he would want to know *now* — a plan filling, a stop hit, a trade resolving, the
  drawdown crossing a floor, or the chain breaking. **Do NOT push a quiet check.** Twelve
  pushes an hour saying "nothing happened" trains him to ignore the one that matters, and
  the tool's own guidance is that an unnecessary notification is annoying in a way that
  accumulates. Quiet checks go to the transcript only.

## Verify the cadence by listing it, never by remembering it

There are three tiers keeping callouts reaching the owner's phone, and at 04:37 on 2026-09-28 I
discovered I had been wrong about all of them at once (N45). The rule that came out of it:

**Before asserting anything about whether the cadence is running, run `CronList`.** One command.
It was available the whole time N42 was being written, and it would have prevented a note, a
commit message and a reply to the owner all claiming a 21-minute blackout that never happened.

| tier | mechanism | interval | survives container restart |
|---|---|---|---|
| primary | CronCreate recurring job (`33ba414e`) | 5 min | **no** — session-only |
| backstop | Routine `trig_01NZGwNRd8mftXdxyLvuVpdD` | hourly | yes |
| fallback | `send_later` chain | 5 min | yes, but self-terminates on a missed re-arm |

- The CronCreate job is the primary. It is session-only but it has fired reliably for hours.
  Session-only does NOT mean it dies between turns — that was an over-generalisation from one
  empty `CronList` at 23:58, which was a different, genuinely lost job.
- **Do not run two 5-minute mechanisms at once.** Both report to the owner's phone, so the
  redundancy costs him a duplicate message every five minutes. If `CronList` shows the `*/5`
  job present, change nothing.
- The `send_later` chain is now the fallback, not the primary. Arm it only if `CronCreate` is
  unavailable, and say that is what you did. It died twice (02:12, 04:07) because the re-arm is
  the last action of a turn, which makes it the first casualty of a turn ending early.
- The hourly Routine repairs the **cron**, not the chain. Its first action is `CronList`.
- Residual exposure, which is real and should be stated rather than hidden: if the container is
  reclaimed, the `*/5` cron dies with it and the worst-case gap is up to one hour, until the
  hourly Routine wakes the session and re-creates it.

## Quote the range endpoints with every location percentage

A location reading is a fraction whose denominator is a trailing window, and that window
migrates. On 2026-09-28 MGC's location went 1.8% -> 5.2% across six minutes while price rose
0.40 points, entirely because the range low re-printed 3.90 lower (N46). A bare percentage is
therefore not comparable between two checks. Always write it as `5.2% of [4178.10, 4303.50]`,
so a reader can see which end moved.

## MEASURED PROHIBITION — do not breakout-enter in the direction of displacement

Added 2026-09-28 after the post-mortem on missing a 3x-ATR bearish day (NOTES.md N194-N199).

**Never enter on a break of a short-term extreme in the direction of an already-established displacement.**
Concretely: when `|close - EMA20| > 0.5 * ATR14` with the EMA20 slope agreeing, do NOT place a stop entry
at the extreme of the last few bars in that same direction. That is the entry the tape invites on a trend
day and it is the entry that loses.

Measured out of sample on `data/archive/` (ends 2026-09-25), pre-registered before the run, 4 cells:

| cell | n | E[R] | t | vs random entry |
|---|---|---|---|---|
| MGC 15m | 121 | −0.3640 | −3.617 | **z = −2.61** |
| MGC 60m | 444 | −0.2757 | −5.082 | **z = −4.72** |
| MNQ 15m | 125 | −0.3595 | −3.632 | **z = −3.25** |
| MNQ 60m | 498 | −0.2257 | −4.331 | **z = −2.97** |

Random entries through the identical exits lose only −0.02 to −0.10R, which is the cost drag. This entry
loses two to seven times that, in **4 of 4 cells**, on both symbols and both frames. MGC 60m alone is
−$25,235 over two years. The harness is `cont1.py`; the placebo control is described in N196.

**Why this is installed when nothing else is.** A prohibition and a permission do not need the same
evidence. A wrong prohibition costs foregone trades; a wrong permission costs money. Nothing in this
repository has ever cleared `free_t` 5.46, so no entry rule gets installed — but a veto at |z| 2.6–4.7
against placebo in every cell tested is worth acting on, and it is the single largest effect this desk has
measured for itself.

**What it does NOT license.** It is not a reason to take the opposite side. That was tested too — FADE-1,
pre-registered, the same rule with the position inverted, on MES and MCL which this desk had never touched:
largest t **+1.245** against a declared 3.0, and MCL's larger 60m cell negative. Inverting raises the win
rate 10–16 points and lowers the payoff, and expectancy lands at zero (rule 3, as a result rather than a
reporting rule). **Do not fade it either. Just do not take that entry.**

## A PENDING PLAN CAN NOW DIE OF DISTANCE, NOT ONLY OF THE CLOCK

Added 2026-09-28 at the account owner's instruction: *"it feels like you are too set in your ways with your
swing, even when it's currently so far from your entry — reevaluate when it starts going too far."*

He was right and the record shows it. **CALL-0001 sat on the book for seventeen hours** as a LONG with its
stop-entry 493.50 points — **6.28 ATR** — above a market that fell all day, reported "live" at every single
check, blocking the book and guaranteed to produce no outcome. Until now the only way a pending plan could
die was its expiry timestamp. **N8 forbids EDITING a plan after watching price. It does not require carrying
a corpse.**

### The threshold is measured, not chosen

P(price touches a level D×ATR away within T bars), ~3,645 origins per symbol, `data/archive` 15m
(ends 2026-09-25, out of sample):

| D (ATR) | T=4 | T=8 | T=16 | T=32 |
|---|---|---|---|---|
| 0.5 | 67.0% | 77.3% | 84.3% | 89.5% |
| 1.0 | 39.7% | 54.9% | 68.6% | 78.4% |
| 2.0 | 12.7% | 25.7% | 43.0% | 59.8% |
| 3.0 | 4.1% | 12.5% | 26.2% | 42.8% |
| 4.0 | 1.9% | 6.2% | 15.7% | 30.7% |
| 6.0 | 0.6% | 2.0% | 6.3% | 15.7% |

MGC reproduces this to within one point in every cell, which is what you expect if it is a property of price
travel rather than of either symbol. Travel scales as √time, so the **10% contour is `D = 1.2 × √T`** — checked
against the table at T = 4, 8, 16 and 32 and landing between 9% and 12% each time.

**THE RULE: void a pending plan when `distance_ATR > 1.2 × √(bars_remaining)`** — under roughly a 1-in-10
chance of being *reached at all*, never mind won.

### Why this is not an N8 edit, and how it is kept honest

- **It can only ever REMOVE a plan.** It cannot move an entry, widen a stop, shift a target or change size,
  so it cannot make any plan fill better or win more. The worst it can do is deny the desk an outcome.
- **It lives in `resolve.py`, not in my hands** (`unreachable()`), so it is applied mechanically to every
  plan on every run and I cannot aim it at the plans I have gone off.
- **Voided plans get their own resolution, `VOID_UNREACHABLE`** — never EXPIRED, never a win or a loss. The
  void RATE is therefore auditable: if this starts retiring plans that would have filled and paid, the
  record will show it, and the rule goes.

### What it does NOT license

It is not permission to abandon a plan that is merely losing, uncomfortable, or contradicted by a fresh
read. Distance and time are the only inputs. A plan inside the contour stays, whatever I have come to think
of it since.

## VOLATILITY STAND-DOWN — when the blind spot is wider than the stop may be

Added 2026-09-28 after the second post-mortem (NOTES.md N212-N214).

The desk resolves on 15m bars against a feed that publishes ~12 minutes late, so **15 to 27 minutes pass
between an event and the desk seeing it.** Measured max adverse excursion inside a 27-minute window (1m
bars, archive, bucketed by the volatility regime in force):

| MNQ ATR14(15m) | median excursion | 90th | P(excursion > the 60-pt cap ceiling) |
|---|---|---|---|
| 22.3–25.5 | 26.25 | 44.25 | **4.4%** |
| 32.5–35.4 | 29.75 | 74.25 | **16.1%** |
| 50.3–58.4 | 42.50 | 82.75 | **22.1%** |
| 58.4–77.5 | 60.00 | 119.50 | **49.6%** |
| ~97.5 (today) | 71.00 | 105.25 | **69.4%** |

**THE RULE: do not place a plan on a symbol when P(blind-spot excursion > the maximum permitted stop)
exceeds 25%.** From the table that is approximately **MNQ ATR14(15m) above 58** and **MGC above 10**.

Re-measure both ATRs every check — that is already required — and state the stand-down explicitly in the
report when it binds, with the ATR beside it. An empty book for this reason is a measured decision and must
be reported as one, never as "no setup".

**Why this is installed when no entry rule is.** A wrong veto costs foregone trades; a wrong permission
costs money. And the failure it prevents is not a bad trade, it is a trade whose outcome is decided in a
window the desk cannot observe — which produces a number in the ledger that measures the feed, not the
method.

## EVERY CHECK EMITS A CARD. The owner reads cards, not reports.

Added 2026-09-28 at the owner's instruction: *"keep in mind that i am busy and i would
typically only look at the call out cards."*

**The failure this fixes.** `card_png.py` renders a PLAN. Between 12:43 and 14:30 the book was
empty, so it rendered nothing, so **the owner received no signal of any kind for nearly two
hours** while this desk wrote long reports into a terminal he was not reading. An empty book
is a decision. A decision that never reaches the person whose account it is has not been
communicated, and the stand-down that produced it may as well not have been measured.

**The rule.** Every check sends at least one card, without exception:

- **Plans exist** → `python3 card_png.py <ids> --scale 3` for every PENDING plan, as before.
- **No plans** → `python3 status_card.py 3 "<the binding reason>"` and send `card_STATUS.png`.

`status_card.py` renders the desk state in the NO TRADE grey (never blue or orange, so it can
never be mistaken for a direction in peripheral vision): time ET, both symbols' price, 15m
headline with its tally, ATR against its stand-down line, book state, the measured ledger,
the binding reason in words, and the seven-frame table. MGC's DAILY cell prints `NOT ELIG`
rather than a headline, because CALLOUT.md §4 forbids using that series.

**ORDER: the card goes LAST, at the bottom of the response.** Owner's instruction,
2026-09-28 14:42. Write the text report first, then send the card as the final act of the
check, so the thing he actually reads is the last thing on his screen rather than buried
above a wall of text he is scrolling past.

**The text report still goes in the terminal and the notes still go in `NOTES.md`** — they are
the record and the record matters. But they are not the delivery. **If a check ends without a
card having been sent, the check did not report, whatever was written.**

## EVERY DECISION IS AN ACTION AND EVERY ACTION HAS A COST. Price it, in `DECISIONS.md`.

Added 2026-09-28 at the owner's instruction: *"every call and stand down is an action you are
making… everything has an opportunity loss and i would like you to reflect everytime you change
your decision or make an update."*

**The omission this fixes was structural, not an oversight of mine on one day.** `journal.jsonl`
records plans, `state.json` records fills, and **nothing recorded a refusal.** Eleven consecutive
checks of "empty book, measured reason" left no trace that a decision had been made at all. A
veto costs nothing to write, so if it is never priced it always looks free, and it therefore
wins every argument against a trade by default. That is an accounting error with a direction.

**The rule.** Every decision gets a row in `DECISIONS.md` carrying three separate numbers:

- **FORECLOSED (upper bound)** — the movement available in the decision's window, in points,
  dollars and R at the maximum permitted stop. Assumes a perfect entry at the turn, which
  nobody gets. Computable from the tape; never an estimate of a trade I did not write.
- **MARGINAL** — the cost *given the rest of the machinery*. If the reversal gate produced no
  unanimous bar in that window, no plan could have existed and the veto's marginal cost is
  **zero**. Stating that is arithmetic, not an excuse.
- **REALIZED** — actual dollars in `state.json`. Only fills produce this.

**Report both the upper bound and the marginal number, always.** Quoting only the marginal is
how a veto flatters itself; quoting only the upper bound is how a trade does.

**A change of mind is a decision too.** Installing a rule, retiring a plan, changing the cadence,
changing what gets reported — each gets a row, and the reflection is part of making the change,
not something added afterwards if there is time.

**On the card.** When a stand-down is binding, the card carries what it has foreclosed so far.
The owner should be able to see the price of the desk's caution without asking for it.

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
python3 workspace/paper/CALL/card_png.py CALL-0001 CALL-0002
```

**One card per symbol, 1700x~1000.** Each call writes its own `card_{SYMBOL}_{call_id}.png`:
symbol top-left at 104px, direction beneath it, the whole card a diagonal gradient in the direction
colour with an outline running the outside, and **Entry / TP1 / SL as three large popout panels** —
those are the three numbers a reader acts on, so those are the three that are big. Secondary
mechanics strip below, then thesis, weakness, confidence. Do not stack calls into one tall image;
a 728x2463 strip is a scroll, not a card, and it buries the number the reader wanted.

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

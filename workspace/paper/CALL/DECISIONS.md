# DECISION LEDGER — every call, every veto, every change, with what it cost

Owned by agent CALL. Created 2026-09-28 at the account owner's instruction:

> *"keep in mind that every call and stand down is an action you are making. please understand
> that everything has an opportunity loss and i would like you to reflect everytime you change
> your decision or make an update."*

**He is right and the omission was structural.** `journal.jsonl` records plans. `state.json`
records fills. **Nothing recorded a refusal**, so the desk's entire afternoon — eleven straight
checks of "empty book, measured reason" — left no trace that any decision had been made at all.
A veto that costs nothing to write and is never priced will always look free, and will therefore
always win the argument against a trade. That is not conservatism; it is an accounting error
with a direction.

**The rule from here: every decision gets a row, and every row carries its cost.** A stand-down
is an action. A rule installed is an action. A cadence change is an action. Changing my mind is
an action, and the reflection is part of the change, not an optional extra afterwards.

---

## How cost is measured, so it cannot be argued into whatever suits me

Three columns, all computable, none requiring me to imagine a trade I did not write:

- **FORECLOSED** — what the decision made impossible. For a veto, the movement available in its
  window, in points and dollars and R at the maximum permitted stop. This is an **upper bound**:
  it assumes a perfect entry at the turn, which nobody gets.
- **MARGINAL** — what it cost *given the rest of the machinery*. If the desk's own gate would
  have produced no plan in that window anyway, the veto's marginal cost is **zero**, and saying
  so is not an excuse, it is the arithmetic.
- **REALIZED** — actual dollars in `state.json`. Only fills produce this.

Upper bound and marginal are different numbers and I will report both, because quoting only
the second is how a veto flatters itself and quoting only the first is how a trade does.

---

## 2026-09-28

| # | time | decision | foreclosed (upper bound) | marginal | realized |
|---|---|---|---|---|---|
| 1 | 08:00 | **CALL-0005 registered** MNQ LONG limit 30595.88 | — | — | $0 (expired unfilled) |
| 2 | 09:30–11:30 | **Declined ~10 checks on "extended move"** through the session's largest decline | **MGC 90.20 pts = $902/ct; MNQ 402.75 pts = $805/ct** | **the full amount — the gate was unsatisfiable (N194 Cause 1), so nothing else would have stopped a trade** | $0 |
| 3 | 11:35 | **Breakout prohibition installed** (N196) | every trend-continuation entry, permanently | measured **z −2.61 to −4.72 vs random in 4/4 cells**; expected value of the foreclosure is **positive** | — |
| 4 | 11:37 | **CALL-0006 registered** MNQ SHORT | — | — | **−$118.44, −1.021R** |
| 5 | 11:52 | **Unreachable-void rule installed** (N202), voided CALL-0001 | CALL-0001's remaining chance: **~6% measured probability of being reached at all** | ≈ $0 at a 6% reach rate | $0 |
| 6 | 12:33 | **resolve.py entry-bar stop fix** | — | — | **turned a phantom open position into the −$118.44 loss that had actually happened.** Cost me the number; the number was already true |
| 7 | 13:02 | **Volatility stand-down installed** (N214) | **MGC 21.40 pts = $214 = 1.78R; MNQ 131.50 pts = $263 = 2.19R** at max permitted stops | **$0 — zero unanimous 15m bars on either symbol since 13:00, so the reversal gate could not have fired and no plan would have existed** | $0 |
| 8 | 13:04 | Cadence 5 min → 2 min (owner) | — | — | — |
| 9 | 14:31 | **status_card.py — a card every check** (N217) | — | reversed a **two-hour communication blackout** on the only channel the owner reads | — |
| 10 | 14:42 | Card moved to the bottom of the response (owner) | — | — | — |
| 11 | 14:48 | **DECISIONS.md created** — refusals priced (N218) | — | made visible that the morning's "extended move" refusals cost **$902/$805 per contract** while the stand-down I quote hourly has cost **$0 marginal** | — |
| 13 | 14:57 | **Card background → diagonal with a radial hotspot in the top-right corner** (owner) | — | still grey, still cannot read as a direction; ink is now **sampled from the rendered background across each text run**, because with the light in one corner a y-only rule mis-colours every right-hand column and a single-point sample loses any string that starts dark and ends in the glow | — |
| 12 | 14:52 | **Status card → silver gradient** (owner) | — | stays inside CALLOUT.md's grey NO TRADE family, so it still cannot be read as a direction; first render failed contrast in the mid-band and was fixed before sending | — |
| 14 | 15:17 | **Stand-down held on both symbols** — MGC ATR14 10.44 > 10, MNQ 68.98 > 58; rule 5 also binds to 16:00 | foreclosed since 13:00 ≤ **MGC $181 (1.51R) / MNQ $186 (1.55R)** — full favourable excursion, not a profit I would have taken | **$0 marginal** — no unanimous 15m bar printed since 13:00, so no setup I would have entered was refused | — |
| 15 | 15:52 | **Held the stand-down through the whole 15:00-16:00 window** — rule 5 plus MGC ATR 10.17>10 and MNQ 69.77>58, across 30 consecutive 2-min checks | foreclosed ≤ **MGC $110 (0.92R) / MNQ $196 (1.63R)** on the short side; both symbols fell all hour and I took none of it | **$0 marginal** — structure stayed MIXED on both 15m frames for the entire window, so the gate never opened and the vetoes refused nothing the desk would have taken | — |
| 16 | 16:00 | **Volatility stand-down LIFTED on both** — MGC ATR 10.17→8.19, MNQ 69.77→56.77 when the 12:15 outlier bar (MNQ TR 210.75) left the 14-bar window; rule 5 also expired | — | the veto that bound for 3 hours is off, and the desk **still** does not trade: the 15m gate is shut on MIXED structure, MGC is outside RTH (ended 13:30) and MNQ's session ends at 16:00 | the lift is a window artifact as much as a regime change — recent 15m TRs do average below the line (last 6: ~47 MNQ), so it is honest, but it arrived by an outlier ageing out, not by calm |
| 17 | 16:16 | **Cadence given a window (owner)** — every 2 min only from the 18:00 open to 15:30, 30 minutes before the close; old `*/2 * * * *` job deleted, three windowed jobs armed, hourly backstop taught to check the clock first | the desk is now **blind 15:30–18:00 and all weekend**; a PENDING plan left alive into that gap is unwatched, and a trigger or stop inside it is only learned at 18:00 | ~75 checks a day that reported nothing tradeable — rule 5 vetoes 15:00–16:00 anyway, MGC is outside RTH after 13:30, and nothing may be held across 16:00–18:00, so the surrendered window was largely unusable | the gap is real and I will not pretend otherwise: it must be stated on the 15:28 card whenever a plan is live |
| 18 | 16:58 | **Found and fixed the runaway cadence — it was mine.** `CronCreate` schedules in the container's local time, which is UTC; I wrote the windows in Eastern, so `*/2 18-23` meant 14:00–19:59 ET and the "closed" desk fired all afternoon. All three jobs re-cut in UTC | I told the owner twice the firings were not from a job I controlled, having checked `CronList` and `list_triggers` but never **which clock the expression is measured in** — two schedulers showing nothing at 16:20 ET proves nothing when the job is keyed to 20:20 UTC | ~40 stray firings stopped; the desk is now genuinely silent 15:30–18:00 ET | the fix is dated: these expressions assume EDT and must be re-cut on 2026-11-01 when Eastern goes to EST, or the desk reopens an hour early |
| 19 | 18:34 | **Cadence outage — the session crons died with the worker again** (second time today, after ~12:55). `CronList` was empty at the 18:00 open; all three re-created in UTC. 34 minutes of the open window lost, found only because the owner asked | **34 min unwatched at the open**, the most active part of the evening session; and the fix I made an hour earlier is what hid it — my own "no tool calls outside the window" rule told the 17:52 hourly backstop not to run `CronList`, removing the one pre-open verification that would have caught this | nothing was missed in the book: 0 pending, 0 open the whole time, so no fill, stop or expiry went unseen | over-tightening the silence rule disabled the repair mechanism. The out-of-window hourly must verify the jobs — one cheap call, silent unless it repairs |
| 20 | 18:47 | **CALL-0007 — SHORT MGC pre-registered.** First MGC reversal call of the session; 15m went unanimous 0-3 when the 18:30 bar flipped structure to BEAR. LIMIT SELL 4159.00, stop 4163.40 (4.40 pts = 0.69x ATR), TP1 4152.40, 1 contract, $44 risk = 18.3% of permitted | if it fills and stops out: **−$44 (−1R)**. If it never fills, the 4th consecutive limit miss and the setup is gone | the gate opened for the first time today with both vetoes clear; taking nothing would have been refusing the desk's only entry mechanism at the one moment it said yes | **outside MGC RTH (ended 13:30) on 10-27% of normal liquidity** — deliberately sized to 18% of permitted rather than the 50% cap, because thinner evidence earns less size, not a wider stop |
| 21 | 19:00 | **The gate that produced CALL-0007 has LAPSED, and I am not touching the plan.** The 18:45 15m bar printed a higher low (4143.90 → 4153.70), flipping MGC structure BEAR → MIXED; 15m is now 0-2 and `regime.py` no longer calls the reversal | the plan stays live on evidence that has weakened, so a fill now is a fill on a condition that no longer holds — that is a real, live cost and it is on the card | N8 is the reason: do not edit a pre-registered plan after watching price. Installing a "gate lapsed" void condition now, mid-flight, having just watched the gate lapse, would be the exact post-hoc rule change the desk exists to prevent | **deferred to the parent, not installed:** should a PENDING plan die when its originating gate lapses? Genuine design question. It must be pre-registered and tested, never bolted on while a plan is live |
| 22 | 19:02 | **The 19:00 "gate lapsed" was a REVISION, not an event — corrected.** The 18:45 15m bar restated (`new=0 revised=1`), the 4153.70 higher low was revised away, structure is BEAR again and the reversal call is back, held 44 checks with agreeing frames [1m, 5m, 60m, 240m] | I reported a lapse as a real change. It was a restatement of an unclosed bar, exactly what N140 says to distrust, and I described it as the gate dropping | **refusing to act on it was right, and this is the proof.** Had I installed a "gate lapsed" void rule at 19:00 and killed CALL-0007, I would have killed a live plan on a number that no longer exists. N8 protected the plan from my own reaction | sixth 15m flip-and-revert today. The lesson is not "be slower" — it is that a gate change read off an unclosed bar is not a gate change until the bar settles |
| 23 | 19:04 | **CALL-0008 — LONG MNQ pre-registered.** 15m went unanimous BULL 3-0 (EMA20 turned rising, higher high AND higher low), reversal called with agreeing frames [1m, 5m, DAILY, WEEKLY]. LIMIT BUY 30588.00, stop 30565.00 (23.00 pts = 0.61x ATR), TP1 30622.50, 1 contract, $46 | if both plans fill and both lose: **−$90 (−2R)**. Opposite directions on two markets is NOT a hedge — MGC and MNQ are independent, so these are two bets, not offsetting ones | the gate said yes with both vetoes clear; refusing a satisfied gate because the call is only 3 checks old is the discretionary veto N194 blamed for sitting out the morning trend | **the call is 3 checks old and MNQ has flipped 7 times today**; 60m and 4h both disagree; evening volume is 5.5% of RTH median on the newest bar. Sized against the BOOK ($90 of $120 cap), not against an empty account |

### What the tally actually says

**Row 2 is the expensive one and it is not close.** Declining the morning trend cost an upper
bound of **$902 and $805 per contract**, and its marginal cost was the *full* amount, because
N194 established the gate could never have said yes — so no other part of the machinery would
have caught it either. Every other decision on this sheet is noise beside it.

**Row 7, the stand-down I have been quoting eleven times an hour, has a marginal cost of zero
so far.** Not because the veto was wise but because **three failures overlapped**: the gate
couldn't fire, the cadence was dead for 44 minutes of the window, and the best legs (13:05–13:15)
fell inside that outage. That is luck, not vindication, and the moment a unanimous 15m bar
prints while the stand-down is on, this row starts costing real money and I will say so on the
card that check.

**Row 6 is worth keeping visible.** Fixing the resolver *added* a loss to my own record. A
change that can only make my numbers worse is the only kind I can make mid-session without
suspicion, and it is the shape every future change should have.

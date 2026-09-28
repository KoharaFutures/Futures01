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

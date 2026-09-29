# Dispatch ledger

One row per dispatch round. The parent session writes this from `get_session` before and after
each round, so the burn rate is measured rather than guessed.

| round | when (UTC) | context before | context after | burn | limit status | dispatched |
|---|---|---|---|---|---|---|
| 0 | 2026-09-27T01:04 | 110,050 (11%) | — | — | allowed | scaffolding only |
| 1 | 2026-09-27T01:04→01:18 | 110,050 (11%) | 143,261 (14%) | 33,211 | allowed | manager, division only |
| 2 | 2026-09-27T01:19 | 143,261 (14%) | — | — | allowed | R1+R2+R3 in parallel |
| 3 | 2026-09-27T03:48 | 490,908 (49%) | — | — | allowed, five_hour resets 08:40Z | EF7+BT4+BT5+BT6+manager; 12 live |
| 4 | 2026-09-27T18:23→18:40 | new session (handoff) | ~190,000 (19%) | ~190,000 | allowed, **five_hour** resets 18:50Z | none — parent-only: the roll and scale audit |

## The window type changed back, and `THROTTLE.md` was stale — recorded 2026-09-27T18:40Z

`rate_limit_info` now reads `rateLimitType: five_hour`, `resetsAt 2026-09-27T18:50:00Z`, `status:
allowed`. `THROTTLE.md` was written when it read `ccr_promotional` with a 39-day reset and says so.
**A five-hour rolling window is a materially different gate:** a round that exhausts it stops
dispatch for *hours*, not for 39 days, so "pause until it refreshes" is a usable throttle again
rather than a research-ending stop. The three checks in `THROTTLE.md` are unchanged and still
correct — `status != allowed` is authoritative, 850k tokens is the context cutoff — but the *cost of
hitting the first one* is now recoverable.

**The previous session lost EF7 to a rate-limit kill.** Under a five-hour window the right response
to `status != allowed` is to bank to disk, commit, and wait, which the promotional window made
pointless. Whoever dispatches the next round should re-read `rate_limit_info` rather than trusting
either version of this note: it has now changed type twice in two days.


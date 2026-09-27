# Dispatch ledger

One row per dispatch round. The parent session writes this from `get_session` before and after
each round, so the burn rate is measured rather than guessed.

| round | when (UTC) | context before | context after | burn | limit status | dispatched |
|---|---|---|---|---|---|---|
| 0 | 2026-09-27T01:04 | 110,050 (11%) | — | — | allowed | scaffolding only |
| 1 | 2026-09-27T01:04→01:18 | 110,050 (11%) | 143,261 (14%) | 33,211 | allowed | manager, division only |
| 2 | 2026-09-27T01:19 | 143,261 (14%) | — | — | allowed | R1+R2+R3 in parallel |
| 3 | 2026-09-27T03:48 | 490,908 (49%) | — | — | allowed, five_hour resets 08:40Z | EF7+BT4+BT5+BT6+manager; 12 live |

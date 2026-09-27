# Dispatch ledger

One row per dispatch round. The parent session writes this from `get_session` before and after
each round, so the burn rate is measured rather than guessed.

| round | when (UTC) | context before | context after | burn | limit status | dispatched |
|---|---|---|---|---|---|---|
| 0 | 2026-09-27T01:04 | 110,050 (11%) | — | — | allowed | scaffolding only |

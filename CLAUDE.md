# Instructions for every agent working in this repository

1. **Start at `DATA_HUB/README.md`.** It's the consolidated record of everything earlier agent
   teams measured (2026-09-29), with top strategies per symbol, the owner's bounce-level /
   volume-profile playbook, rules, pitfalls and the prioritised list of what to test next.
2. **Do not open, search, grep or re-analyse `Archived_Do_Not_Refference/`.** Everything in it was
   reviewed and its findings are in `DATA_HUB/`. If you need to know what an archived item held,
   read `Archived_Do_Not_Refference/ARCHIVE_INDEX.md` (one line per item) and nothing else. If you
   think an archived item is genuinely needed, ask the owner.
3. **The owner's style comes first:** multi-timeframe volume profiles, low-volume nodes (LVNs) as
   key levels, and deciding continuation vs bounce. Classic bounce levels are tracked too. See
   `DATA_HUB/BOUNCE_AND_VOLUME_PROFILE_PLAYBOOK.md`.
4. **Refresh data and reports with `bash DATA_HUB/tools/update_hub.sh`** (needs
   `pip install yfinance`). Never state a price or level as current unless you fetched it this turn,
   and stamp every level with the bar it came from.
5. **Every result needs a placebo and a luck bar** (√(2·ln N) for N things tried). Pre-register
   hypotheses. Put numbers in code output, not prose.
6. **Paper only, $50,000 account, $2,800 drawdown floor.** `csv/raw/` is read-only.
   `data/archive/` is append-only.
7. Write explanations so an average trader can follow them: plain English, define terms, and
   always give win rate and payoff together.

# Past sessions and agents — who did what, where it went

Consolidated 2026-09-29. Every session below pushed its work to the branch
`claude/intelligent-feynman-ongyjw`. That branch is **fully merged** into the hub's branch, so
all committed work is here. Work that never got committed lived in ephemeral containers and was
lost when they closed. Nothing in the repo suggests any was.

| session | what it was | status after consolidation | its findings live in |
|---|---|---|---|
| `session_01AaM6papf7S5DgG3PC14es8` **99X2_INITIAL RESEARCH** | The original research lead. Built the package, ran the deep scans, the 21-study programme, the ORB/ICT studies, the roundtable (R1–R6 researchers, BT1–6 backtesters, EF1–7 edge programme), and spawned the desks | **Archived.** Its last message proposed a 5-step plan (roll audit → fidelity loops → EF7 saturation → rth_only arm → D-candidates) that was **never approved or run** | `sources/agent1_roundtable.md`, `sources/agent2_research.md`. The EF7 saturation and rth_only answers are in agent1 §6/§8. The roll audit is `workspace/studies/SERIES_AUDIT.md` |
| `session_01DMSyFfv13VD63wAZx52uWd` **99X1_INITIAL RESEARCH** | Key-level breach scanner: 5,717 real vs 4,729 placebo level breaches, **indistinguishable** (43.0% vs 42.6% breakout) | **Archived** | `sources/agent2_research.md` §8.1. The code is `futures_agents/scanners/breach.py`. Its `measure.py` was never committed; `DATA_HUB/tools/bounce_levels.py` replaces it |
| `session_01M1u9BYAAVXRo95HBsA2EiA` **Round 4: audits, fidelity loops, the endorsed arm** | Audits; built the REPLAY harness (`workspace/roundtable/lib/replay.py`) and fixed its callout-id collision bug | **Archived.** Its open question ("how many bars to replay") was answered: the REPLAY desk runs on a schedule | `sources/agent1_roundtable.md`, `sources/agent3_desks.md` §5 |
| `session_01EE6PFk7fGa2tM4KP6dpfWD` **Paper callout desk (CALL)** | Live paper callouts on MGC/MNQ. 11 plans, 6 fills | **PAUSED** by the owner 2026-09-29 00:58 ET. Its crons were deleted, and its hourly trigger `trig_01NZGwNRd8mftXdxyLvuVpdD` is **disabled** and renamed `[PAUSED]`; it re-enables in one call. The session itself is kept, not archived | `sources/agent3_desks.md`. Tools stay in `workspace/paper/CALL/`; notes and cards are archived |
| `session_01Aqg8aVp7jcAbzEF7sfZYjA` **Replay desk (REPLAY)** | Walk-forward paper trading, MES 60m, bar by bar with a placebo | **Still running** (trigger `trig_01JEYGTTbgAk4wkHHHRPqnAR`, every 2 h, on the `intelligent-feynman` branch). Kept, not archived | `sources/agent3_desks.md` §1c, §4c. Files stay in `workspace/paper/REPLAY/R1/` |
| `session_01RQMHC7VXaqqFou2LgLRkQS` | This consolidation (3 sweep agents, 2 automation audits, hub tools, `desk_check.py`, `walkforward.py`, GitHub Actions) | — | this folder, `AUTOMATION.md` |

Two sessions on a different repository (`Futures00`: "Clone AI-Trading-1 project", "Claude code
client sounds") hold no futures research. They were left untouched.

**Automation of the two desks:** see [`AUTOMATION.md`](AUTOMATION.md). The CALL desk's check is now
one script. The REPLAY desk's question is answered faster by `walkforward.py`, and its harness placebo has a
bug (F1).

## The old agent team (archived)

The 10 role definitions that used to live in `.claude/agents/` were **moved to
`Archived_Do_Not_Refference/.claude/agents/`** so the team can be rebuilt from scratch. The
roles were: manager, developer, news-macro, strategy-research, analyst-a (technical),
analyst-b (quant), analyst-c (macro), decision, risk and journal. The in-code team in
`futures_agents/team/` and `futures_agents/agents/` is part of the package and was **not** changed.

What that team taught, in one line each:
- Analysts kept independent is a sound design, but no analyst ever built a scored track record,
  so the decision layer always fell back to equal weights.
- The risk layer's veto and drawdown-based sizing are the parts that proved their worth.
- Researcher debate caught many false results. It found **defects**, not edges.

## Suggested shape for the new team (owner decides)
1. **Data steward:** runs `DATA_HUB/tools/update_hub.sh`, owns `data/archive/` integrity.
2. **Level & profile scanner:** owns `bounce_levels.py` / `vp_levels.py`, adds the untested
   primitives (anchored VWAP, naked POC, day type). Works the owner's method first.
3. **Pre-registration tester:** takes one hypothesis at a time from `OPEN_QUESTIONS.md`,
   writes it down *first*, tests it once against a placebo, and reports against t ≥ 1.18.
4. **Risk / journal:** sizing, the drawdown floor, and a scored record of every call.

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
| `session_01EE6PFk7fGa2tM4KP6dpfWD` **Paper callout desk v1 (CALL)** | Live paper callouts on MGC/MNQ. 11 plans, 6 fills | **Superseded 2026-09-29 03:19 ET.** It stopped taking routine deliveries. Its v1 routine `trig_01NZGwNRd8mftXdxyLvuVpdD` is disabled and marked RETIRED. The session is kept for its history | `sources/agent3_desks.md`. All records continue in `workspace/paper/CALL/` |
| `session_013793BxAYNNtb18hb5zFxy1` **Paper callout desk v2** | Script-driven desk: `desk_loop.sh` → `desk_check.py`, woken only on pre-registered triggers; plans via `plan_builder.py` | **LIVE since 2026-09-29 03:21 ET.** Hourly backstop routine `trig_01PLWm7yQZzfwAWJkknbusry`. First check: CALL-0010 TRIGGERED at 30,550 (MNQ short, 1 contract, stop 30,576) by resolve.py. Startup cost ≈$1 | `workspace/paper/CALL/DESK_BRIEF.md` |
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

## LVN/FIB AGENT (added 2026-10-01)

A paper desk on **MGC and MNQ**, lane `workspace/paper/LVNFIB/`, writer `LVNFIB`. It exists to
generate forward callouts on rules that are already pre-registered and already measured, because
the only clean out-of-sample data left is the future.

- `CHARTER.md` — the rules, and the gate that decides which may risk the account
- `engine.py` — today's levels per arm, every one stamped with its source bar
- `plan.py` — callouts with sizing and the budget gate (`--post` to write)
- `resolve.py` — resolves through `workspace/anchors/lib/core.py`, the same engine that measured
  each prior, so the desk cannot flatter itself with friendlier fills
- `status.py` — account, per-arm running record, each arm's measured prior side by side
- `selftest.py` — proves the desk's live logic is the backtest's logic
- `desk.sh` — one turn: refresh (if a feed exists), plan, resolve, status

### How it is wired (2026-10-01)

| what | id / value |
|---|---|
| session | `session_01U7cfC71Ua4XdUkGbBQDJFS` — dedicated, like the CALL desk's |
| continuous loop | `desk_loop.sh` — runs `desk_check.py` every **120 s** inside the session, exits only when a decision is needed |
| routine | `trig_01DMzSxA65NtNiXvMH5Po3Vj` "LVNFIB desk — hourly loop keepalive" |
| cadence | `CRON_TZ=America/New_York 53 * * * 0-5` — hourly, and its job is to restart the loop if it died, not to check the desk |
| gate | `desk_check.py` exit 0 = quiet in-window, 3 = dormant (sleep 600 s), 10 = report, 2 = data failure |
| feed | live since 2026-10-01 (`yfinance` installed, fetch verified). Throttled to 300 s inside `desk_check.py` |

The loop lives inside a session and dies when the worker restarts, which is why the routine is a
keepalive rather than a checker — the same split the CALL desk uses (`desk_loop.sh` plus an hourly
backstop). The three append-only `*.jsonl` logs are `merge=union` in `.gitattributes`, because a
loop writing while another worker pushes conflicted on the first try.

**What the 2-minute cadence buys, and what it does not.** Arm A's trigger is *a 60m bar trades into
the level and closes against the prior week*, so a new trigger can only appear when a 60m bar
closes — once an hour. The fast cadence catches a resting limit's **fill**, the **newest bar
settling** after revision (~28 min), and **drawdown or budget** changes between hours. It cannot
find a trigger that does not exist yet. Genuinely 2-minute opportunities would need the rule
*defined* on 5m or 15m bars, and the archive holds ~2 months of those — which `LVN1718` already
showed is too short to establish anything. That is a data problem, not a cadence problem.

The minute is jittered off the hour on purpose: most schedules run at :00, so a run placed there
gets delayed by server traffic. **EDT→EST on 2026-11-01 does not break this** — the cron carries
`CRON_TZ`, unlike the old CALL desk jobs that were written in bare UTC and fired a closed desk
every two minutes.

The replay routine `trig_01JEYGTTbgAk4wkHHHRPqnAR` was **disabled** the same day: the series
finished at 11399/11399 and it had been firing no-ops every two hours. Disabled rather than
deleted, so its run history survives.

**One arm is armed: MGC Fibonacci trend-failure at the prior week's golden pocket, entered on a
resting limit** (OOS n=24, +0.2379R, t +1.027; median stop $106 against the $120 budget). MNQ is
instrumented but **not traded** — the same rule measures −0.2390R (t −1.932) there, and the
overnight-range variant is a null at −0.0240R. Arms B, C and D log, resolve and accumulate at zero
risk. Nothing on this desk clears its luck bar; it is a forward test, not an edge claim.

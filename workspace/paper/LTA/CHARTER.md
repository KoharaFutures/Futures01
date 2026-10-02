# LTA CONCEPT CALLOUTS — paper desk charter

**Paper only. $50,000 account, $2,800 drawdown floor.** Lane `workspace/paper/LTA/**`, writer `LTA`.
Symbols: MNQ, MES, MGC, MCL. MES and MNQ are one index complex, so a callout on both counts as one bet.

**This desk trades the LTA book and nothing else.** It is separate from the other desks
(LVNFIB, CALL, REPLAY): it shares none of their rules, levels, state, journals or branch.
The only rules in common are the account rules every desk follows (CLAUDE.md #6: paper,
$50,000, $2,800 floor; the owner's session window: flat by 16:00 ET, nothing held 16:00–18:00).
What other desks measured is kept in `DATA_HUB/LTA_CONCEPTS.md` §10 as background reading only.
It is never a gate here.

This desk calls out trades the way the *LTA Concepts 2.0* book does: layered top-down, executed
on volume-profile levels with four entry models, managed with the 2/2/2 rule. The concepts are in
[`DATA_HUB/LTA_CONCEPTS.md`](../../../DATA_HUB/LTA_CONCEPTS.md). **Nothing on this desk has a
measured edge.** Every card says `PAPER — UNVALIDATED` and `confidence DISCRETIONARY`.

## 1. The callout procedure (every time, in this order)

1. **Fetch or say you didn't.** Run `bash workspace/paper/LTA/desk.sh` (it pulls bars when
   `yfinance` is installed). If the fetch fails, every level is an archive level and the card says
   so. Never call a level "current" unless it was fetched this turn or the owner quoted it.
2. **Macro layer** (`macro.py`): macro trend, valuation (counted only with the trend and a usable
   correlation), seasonality (book window plus own 5y/10y count), COT from `cot_inputs.json` or `UNKNOWN`.
   Result: BULLISH / BEARISH / NONE.
3. **Macro technical:** name the higher-timeframe supply or demand zone (monthly → 8h) price is
   in or heading to, using the book's RBR/DBD/DBR/RBD patterns and the three-candle bar play.
   Note whether a zone just **took out** an opposite zone (macro structural shift).
4. **Intraday trend** (`lta_levels.py`): 60m/30m two-touch trend, break of structure, position vs
   the prior week's range (above PWH / below PWL = momentum side), vs PD value, vs SO.
   Without a break of structure you are in the **preparation phase**: plan only.
5. **Scenario map** at the zone: sharp rejection = go to the lower timeframe; slow grind = wait;
   clean break plus a structure shift = drop the idea.
6. **Execution:** an entry model (EM1–EM4) at a named level, on 15m–1h. `lta_levels.py` lists
   mechanical candidates. The agent confirms or rejects them by reading the bars. Then run
   `callout.py` with the numbers. Its gates are binding.
7. **Archetype and risk:** CONTRARIAN (against the macro or intraday trend, or no macro bias) →
   half risk, BE at +1R. MOMENTUM (all aligned) → full risk, no BE. If the zone is unconfirmed → half risk.
8. **Card and journal:** post with `--post` only when the owner wants it on the record.
   `ledger.py` resolves posted cards against later bars and keeps the record.

## 2. Gates that `callout.py` enforces

| gate | rule | source |
|---|---|---|
| stale data | newest bar > 2.5 h old → refuse unless the owner quoted the price | CLAUDE.md #4 |
| session window | nothing opened 15:30–18:00 ET, flat by 16:00, weekend closed | owner's window (all desks) |
| candle close | not in the last 10 min of a 30m/60m candle (the scanner acts on closed bars) | book p73 |
| reward | target ≥ 2R (default exactly 2R) | book 2/2/2 #1, p219 |
| risk budget | **full = min(0.5% equity, 10% of room to the floor)**; **half** for contrarian or unconfirmed | book 2/2/2 #2, mapped to this account (§3) |
| two strikes | two losses in a row today and the day not green → HALT for the day | book 2/2/2 #3, p222 |
| floor | no trade at or below the $2,800 drawdown floor | CLAUDE.md #6 |
| obstacle | a key level within the first 1R of the path → NO TRADE | book p79 |
| notes | CONFLUENCE (levels lining up), correlated follow-up after a loss, news within 60 min, Mon/Tue trap risk | book p48, p222, p73, p43 |

## 3. Why the book's 2% became 0.5%

At 2% ($1,000) the $2,800 floor is three losses away. At the full budget here ($250 on day one,
shrinking as drawdown eats the room) it is more than ten. The repo's one result that clears its own
threshold is that **size-shrinking governors protect the account** (|z| 6.16). The book's structure is
kept (full vs half, the 2:1 ratio, two strikes) and only the scale changes. Size never rises until
30 rule-following trades are on the record (book p222, p237). After that it still waits for a placebo.

## 4. What the card always carries

`PAPER — UNVALIDATED` · confidence `DISCRETIONARY` · the as-of bar · the entry model, timeframe and
level with the level's source bar · archetype · macro bias · intraday trend · entry, stop, target,
R:R · contracts, $ risk and budget (full or half) · equity and room to the floor · obstacles in the
path · every refusal and warning · management rules · the thesis, written before the outcome.

## 5. Pre-registered tests (written before anyone has run them)

These turn the book's claims into questions this repo can answer. Each is run once,
against a placebo, with the luck bar for **N = 5** tests here: √(2·ln 5) = **1.79**. A test passes only
if real beats placebo by more than that. Until one passes, the desk stays `DISCRETIONARY`.

| id | hypothesis (book page) | real | placebo |
|---|---|---|---|
| **LTA-H1** | EM1 at PD POC/VAH/VAL on 30m **in the direction of the 60m two-touch trend**, stop beyond both wicks, 2R target, flat 16:00, earns more than the same pattern at random prices inside PD's range (p67, p72) | EM1 at PD levels | EM1 at random prices in the PD range, same bars |
| **LTA-H2** | A weekday **Monday/Tuesday** break of PWH/PWL fails (closes back inside within 2 sessions) more often than a Wed–Fri break (p42–p43) | Mon/Tue breaks | Wed–Fri breaks, and random-weekday labels |
| **LTA-H3** | An Asia-session dip below the **Sunday Open** that is reclaimed by London's close → long to 2R beats the same trade at a random weekly price (p44) | SO reclaim | reclaim of a random price inside Monday's Asia range |
| **LTA-H4** | EM1 at PD levels **while price is outside the prior week's range** (momentum side) beats EM1 while inside it (p183–p184) | outside-PW-range EM1 | inside-range EM1, and random-level EM1 |
| **LTA-H5** | For contrarian-tagged trades, **BE at +1R** improves expectancy over no BE (p229) | BE at 1R | the same trades with no BE (paired) |

Data: `data/archive` 60m runs 2024-10 → now; 5m and 30m only about two months, so H1/H3/H4 on 30m have
small samples and must report n. Costs from `futures_agents.config`. Report win rate **with**
payoff, n, mean R, t, and the luck bar, in code output (`walkforward.py` style), not in prose.

## 6. Known limits

- COT/OI layers depend on the owner: cftc.gov is blocked by this environment's network policy.
- Yahoo bars lag about 13 min at 5m and the newest 1–2 bars revise for about 28 min. Setups on the newest bar are
  flagged `UNSETTLED`.
- The macro trend, correlation cut-off (|r| ≥ 0.30) and valuation extreme (±80) are this desk's
  own pre-registered stand-ins. The book gives no numbers for them.
- `ledger.py` resolves pessimistically (a bar touching both stop and target counts as the stop) and
  assumes the quoted entry was fillable.

## 7. The 2-minute scan (`scan.py`, run by `cycle.sh`)

Every 2 minutes the desk runs the book's process on MNQ, MES, MGC and MCL by itself:

1. **Dormant** on the weekend, and from 16:00 to 18:00 ET when nothing is open (no fetch). Exit 3.
2. **Fetch** fresh 5/15/30/60m bars into `live/` (at most every 100 s). It never writes `data/archive/`.
3. **Macro bias** per symbol (refreshed hourly): valuation (with the macro trend and the correlation
   gate), seasonality, and the owner's COT read from `cot_inputs.json`.
4. **War map**, then the entry-model candidates (EM1/EM3/EM4) that completed on the **bar that just
   closed** (30m or 60m). Each one must pass the book's filters:
   - **F1** the level is a book execution level: PD/EPD/PW/EPW/CW/Swing POC, VAH or VAL, SO or PSO [p66–p80]
   - **F2** the side agrees with the 60m or 30m two-touch intraday trend [p180–p182]
   - **F3** Asia session (18:00–02:00 ET) is low volume, so only 60m confirmations count [p73]
   - **F4** one position per symbol, and MES/MNQ count as one bet [p222]

   Then every §2 gate applies. Archetype and risk come from the macro bias:
   - macro bias agrees with the side → MOMENTUM, full risk
   - macro bias is NONE or against the side → CONTRARIAN, half risk, BE at +1R
5. **Post** passing callouts to `callouts.jsonl` and draw a **PNG card** in `cards/`. Setups that were
   filtered or refused are logged in `scan_events.jsonl` (local) and are not sent.
6. **Resolve** open positions on 5m bars and draw the outcome card.

Exit codes: 0 quiet · 3 dormant · **10 notify** (each `CARD <path>` line is a PNG to send the owner) · 2 data failure.
On exit 10, `cycle.sh` commits the lane and pushes this desk's branch.

**Known limit:** while COT is `UNKNOWN`, the macro bias is mostly NONE, so most scanned trades are
CONTRARIAN at half risk ($125). On MNQ a 60m stop usually costs more than that, so MNQ/MES
callouts are often refused for size. That is the book's rule applied to this account, and it is not a fault.

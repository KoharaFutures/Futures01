# LTA CONCEPT CALLOUTS

Paper callout desk that applies the **LTA Concepts 2.0** framework (macro bias → higher-timeframe
zone → intraday trend → volume-profile level + entry model → 2/2/2 risk) to MNQ, MES, MGC and MCL.
Read [`CHARTER.md`](CHARTER.md) for the rules and [`study/CONCEPTS_DIGEST.md`](../../../study/CONCEPTS_DIGEST.md)
for the concepts. The agent definition is [`.claude/agents/lta-concept-callouts.md`](../.claude/agents/lta-concept-callouts.md).

```bash
pip install yfinance                                   # once per container
bash desk/cycle.sh                      # the 2-minute scan (what the schedule runs)
bash desk/desk.sh                       # fetch → macro → war map → resolve → status
bash desk/desk.sh --no-fetch MGC        # archive only (levels are NOT live)
python3 desk/lta_levels.py --symbols MNQ      # the LTA level map + entry-model candidates
python3 desk/macro.py --symbols MGC           # valuation, correlation gate, seasonality, COT
python3 desk/callout.py --symbol MGC --side SHORT --entry 4205.7 --stop 4214.2 \
    --model EM1 --tf 30m --level "PD VAH" --macro BEARISH --htf "daily supply 4210-4232" --why "..."   # dry run
python3 desk/ledger.py                  # resolve posted callouts, print the record
```

| file | what it is |
|---|---|
| `CHARTER.md` | procedure, gates, the 2%→0.5% mapping, pre-registered tests LTA-H1…H5 |
| `lta_levels.py` | SO/PSO, PD/EPD, PW/EPW/CW and swing profiles, PDH/PDL/PWH/PWL/PWC, intraday trend, weekly-cycle phase, STACKED flags, EM1/EM3/EM4 candidates, every level stamped with its source bar |
| `macro.py` | macro trend, valuation vs DXY / ZB, correlation gate, seasonality (book window + own count), COT from `cot_inputs.json` |
| `cot_inputs.example.json` | template for the owner's COT/sentiment reads (cftc.gov is blocked here) |
| `callout.py` | builds the card, applies every gate, sizes, renders blue/orange/grey, `--post` journals |
| `ledger.py` | resolves journaled callouts on 5m bars, keeps equity / drawdown / two-strike state, win rate with payoff |
| `lta_common.py` | bars, trading day, ATR, volume profile, swing legs, contract specs, terminal alert: everything the desk needs, in one file |
| `fetch.py` | pulls fresh 5/15/30/60m bars into `live/` (git-ignored). the optional `archive/` folder is never rewritten |
| `desk.sh` | one full turn, for a human |
| `scan.py` | **the 2-minute scan**: the book's filters on each freshly closed 30m/60m bar, posts callouts, resolves positions, exit 10 = notify |
| `cycle.sh` | what the 2-minute schedule runs: `scan.py`, then commit + push this desk's branch when something happened |
| `card_png.py` | the PNG callout card (blue long / orange short / grey closed) → `cards/` |
| `callouts.jsonl`, `resolutions.jsonl` | append-only journals (created on first `--post`) |
| `levels/` | last written war maps (`desk.sh` writes them) |

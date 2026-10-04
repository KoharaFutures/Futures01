# LTA-Concepts

Study notes and a paper callout desk for the **LTA Concepts 2.0** e-book ("The Trading War Map",
Lorenzo Corrado). This repo stands on its own: it doesn't import from or share rules with any other repo.

| folder | what's in it |
|---|---|
| [`study/`](study/README.md) | what we learn from the book: the full concept digest, the study tracker and section-by-section notes |
| [`desk/`](desk/README.md) | the **LTA Concept Callouts** paper desk: LTA levels, macro layer, gated callouts, PNG cards, 2-minute scan |
| `.claude/agents/lta-concept-callouts.md` | the agent definition |

```bash
pip install -r requirements.txt
bash desk/desk.sh                 # fetch → macro → LTA level map → resolve → record
bash desk/cycle.sh                # one 2-minute scan cycle (exit 10 = a callout or outcome to send)
```

**Paper only. $50,000 account, $2,800 drawdown floor.** The book's PDF is never committed. Nothing here
has a measured edge yet: every callout is `PAPER — UNVALIDATED · DISCRETIONARY`.

_Study material and decision support, not financial advice._

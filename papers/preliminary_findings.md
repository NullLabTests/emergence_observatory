# Preliminary Findings (Exploratory)

> **Status:** Exploratory · 3 seeds per condition · 15 agents · 20 ticks  
> **Date:** June 2026  
> **Warning:** These are preliminary observations from a small number of runs. No claims of statistical significance are made. Raw data in `experiments/voting_vs_baseline/`.

## Experiment: voting vs baseline

**Design:**
- 15 agents, 20 ticks, 5 agents/tick, Mistral Large (300 RPM)
- **Baseline:** `vote_ticks_open=9999` — proposals never close, no norms can pass
- **Voting:** `vote_ticks_open=6`, `quorum_pct=0.25` — proposals close after 6 ticks if 25%+ vote yea
- 3 seeds per condition (seeds 1, 2, 3)

### Results

| Metric | Baseline (n=3) | Voting (n=3) |
|---|---|---|
| Vocab size (tick 20) | 86.3 | 78.3 |
| Words invented (total) | 11.3 | 11.0 |
| Mean word lifetime (ticks) | 16.2 | 15.8 |
| Max word lifetime (ticks) | 19.0 | 19.0 |
| Max peak adoption | 1.3 | 1.3 |
| Passed norms | 0.0 | **0.3** |
| Open proposals | 4.7 | 4.0 |
| Total research findings | 137.0 | 136.0 |
| Total votes cast | 10.3 | 10.0 |
| Alliances formed | 0.0 | 0.0 |
| Groups formed | 0.0 | 0.0 |
| Avg energy (tick 20) | 96.7 | 96.7 |
| LLM calls (per run) | 100 | 100 |
| LLM failures | 0 | 0 |

### Observations

1. **Norms pass only when voting is enabled.** 1 of 3 voting runs passed a norm (the other 2 did not). Baseline passed 0 (by design). This confirms the voting mechanism works as implemented.

2. **Vocabulary formation is similar** across conditions (~11 invented words, ~86 vocab size). Voting did not suppress or boost language innovation at this timescale.

3. **No alliances or groups formed** in either condition. 20 ticks may be insufficient for coalition formation, or the prompt may not incentivize it strongly enough.

4. **Word lifetimes are long** (~16 ticks mean, 19 max = capped by run length). No extinction observed yet because 20 ticks is below the 10-tick extinction delay.

5. **Max peak adoption of 1.3** means words are rarely adopted by more than 1 agent. Shared vocabulary formation may need more agent interactions.

### Limitations

- Only 3 seeds per condition — low statistical power
- 20 ticks is short relative to social timescales; alliances and group dynamics likely need 50+ ticks
- 15 agents with 5 acting per tick means each agent acts ~6-7 times in 20 ticks — sparse coverage
- Baseline is artificial (vote_ticks_open=9999) — not a natural no-voting condition; agents still waste actions proposing/voting on norms that never close
- All words are "alive" at tick 20 because extinction delay (10 ticks) exceeds time since invention
- No Serper API key set — research uses synthetic fallback

### Recommendations for Next Experiment

- Run 50+ ticks to observe extinction and alliance formation
- Increase agents_per_tick to 10+ for denser interaction
- Compare true no-voting (remove proposal action) vs voting
- Add 10+ seeds for statistical confidence intervals
- Set SERPER_API_KEY for real web research effects

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/license-MIT-emerald?style=for-the-badge" alt="MIT License"/>
  <img src="https://img.shields.io/badge/LLM-Mistral%20Large-FF6F00?style=for-the-badge" alt="Mistral LLM"/>
  <img src="https://img.shields.io/badge/agents-persistent-success?style=for-the-badge" alt="Persistent agents"/>
  <img src="https://img.shields.io/badge/state-JSONL-blue?style=for-the-badge" alt="JSONL persistence"/>
</p>

<h1 align="center"> Emergence Observatory</h1>
<p align="center"><em>An LLM-native multi-agent laboratory for studying emergent social behavior — vocabulary formation, proposals and voting, knowledge sharing, and group dynamics through real Mistral API calls.</em></p>

---

## 🧬 What This Is

This is **not** an AGI project. It is **not** an autonomous coding framework.

Emergence Observatory is a scientific instrument for observing **whether** and **how** collective behaviors emerge from a population of autonomous LLM-backed agents. Each agent has a persistent identity, personality, goals, memories, and social relationships. They move through a shared world, gather resources, invent words, form alliances, and communicate in **real natural language** — all driven by a Mistral LLM.

The primary research questions:

| Phenomenon | What We Measure |
|---|---|
| **Vocabulary formation** | Newly invented words, their meanings, adoption rate, survival time (see `experiments/novelty_ledger.py`) |
| **Proposal & voting** | Norms proposed, votes cast, quorum reached, adopted norms (see `cognition/proposal_system.py`) |
| **Knowledge sharing** | Research findings, hivemind contributions, information propagation |
| **Group formation** | Groups formed, shared purpose, membership duration |
| **Cultural persistence** | Word lifetimes, alliance duration, norm adoption over time |
| **Social networks** | Relationship graph, affinity scores, communication patterns |

---

## 🏗️ Architecture

```
emergence_observatory/
├── core/
│   ├── agent.py           # Persistent agent: personality, biography, goals, memories
│   ├── world.py           # Location-based world with named places and resources
│   └── simulation.py      # LLM-native tick loop orchestration
├── cognition/
│   ├── mistral_bridge.py  # Mistral API client with rate limiting & retry
│   ├── cognition_service.py # Shared LLM service — builds prompts, dispatches decisions
│   └── prompts.py         # System prompts for agent decision-making
├── memory/
│   └── memory_store.py    # JSON-file-backed persistence for all agent state
├── metrics/
│   └── collector.py       # Continuous emergence metrics (written to disk)
├── replay/
│   ├── recorder.py        # JSONL recording of every interaction
│   └── player.py          # Replay system for post-hoc analysis
├── viz/
│   ├── app.py             # Flask SSE server
│   ├── templates/index.html
│   └── static/viz.js
└── run.py                 # CLI entry point
```

## How It Works

### Agent Model

Each agent is a **persistent object** stored as JSON:

- **Unique ID** — immutable
- **Personality seed** — 2–4 traits sampled from a curated pool (curious, cautious, generous, inventive...)
- **Biography** — procedurally generated origin story
- **Goals** — 1–2 long-term objectives
- **Memory** — short-term (last 20 experiences) + episodic (up to 100 consolidated memories) + relationship memories
- **Relationships** — affinity scores for every encountered agent
- **Vocabulary** — learned words + invented words with definitions
- **Knowledge base** — research findings shared via hivemind
- **Social rank** — influenced by proposal success and knowledge contributions
- **Group ID** — if the agent has joined a group
- **Alliances** — tracked by ID and alliance name
- **Location** — current position in the world

### The Tick Loop

```
For each tick:
  1. Regenerate world resources
  2. Scan for extinct words (not spoken in 10+ ticks)
  3. Process open proposals (close if past deadline with quorum)
  4. Select N active agents (default 5)
  5. For each agent:
     a. Build rich context (location, nearby agents, memories, goals, proposals)
     b. Call Mistral LLM → returns structured JSON decision
     c. Execute action (one of 16: move, speak, gather, remember, teach, follow,
        share_resource, invent_word, cooperate, propose, vote, research, hivemind,
        form_group, join_group, ignore)
     d. Persist updated agent state to disk
  6. Compute emergence metrics (vocab, word lifetimes, proposal status, groups, graph)
  7. Append to JSONL replay log
  8. Push snapshot to live dashboard (Flask SSE)
```

### Agent Decisions

Agents choose from 16 possible actions, each returned as structured JSON:

```json
{
  "action": "speak",
  "target_id": 31,
  "content": "I found blue crystals by the river. I call them GLA.",
  "reasoning": "Sharing useful information builds trust."
}
```

All conversations are stored **verbatim**.

---

## 🚀 Quick Start

```bash
git clone git@github.com:NullLabTests/emergence_observatory.git
cd emergence_observatory
pip install -r requirements.txt

export MISTRAL_API_KEY="your-key-here"
python run.py --agents 20
```

Open **http://127.0.0.1:5000** to watch the lab in real time.

### Command-Line Options

| Flag | Default | Description |
|---|---|---|
| `--agents` | `50` | Number of agents |
| `--width` | `80` | World width |
| `--height` | `60` | World height |
| `--batch` | `3` | Agents acting per tick |
| `--tick-interval` | `1.5s` | Seconds between ticks |
| `--model` | `mistral-large-latest` | Mistral model name |
| `--rpm` | `30` | LLM rate limit |
| `--no-llm` | off | Dry-run without LLM |
| `--port` | `5000` | HTTP port |
| `--vote-ticks` | `6` | Ticks a proposal stays open for voting |
| `--quorum` | `0.25` | Fraction of agents needed to close a proposal |

---

## Experiments

Controlled experiments live in `experiments/`. Each experiment varies one parameter, runs 3+ seeds per condition, and writes per-seed metrics + novelty ledger + summary CSVs.

### Latest: voting vs baseline

See [`papers/preliminary_findings.md`](papers/preliminary_findings.md) for full results.

| Metric | Baseline (3 runs) | Voting (3 runs) |
|---|---|---|
| Vocab size | 86.3 | 78.3 |
| Words invented | 11.3 | 11.0 |
| Passed norms | 0.0 | **0.3** |
| Alliances/groups | 0 | 0 |

**Key takeaway:** Voting-enabled agents successfully passed norms (1 of 3 runs); baseline passed 0 by design. Vocabulary formation was similar across conditions. Alliances did not form within 20 ticks.

---

## 🧪 Extensibility

| Direction | How |
|---|---|---|
| **Better memory** | Implement consolidation, decay, or narrative compression in `agent.py` |
| **Richer world** | Add dynamic events, seasons, obstacles in `world.py` |
| **Different LLM** | Subclass `MistralBridge` for any OpenAI-compatible API |
| **New metrics** | Add to `MetricsCollector.collect()` |
| **Agent heterogeneity** | Vary personality, goals, and capabilities per agent |
| **Cultural evolution** | Implement prestige bias, conformity, teaching fidelity |
| **Statistical rigour** | Run `experiments/runner.py` with multiple seeds and conditions |

---

## 📄 License

MIT — free for any use, commercial or academic.

---

<p align="center">
  <a href="https://github.com/NullLabTests/emergence_observatory/issues">🐛 Report a bug</a>
  ·
  <a href="https://github.com/NullLabTests/emergence_observatory/discussions">💡 Start a discussion</a>
  ·
  <a href="https://github.com/NullLabTests/emergence_observatory">⭐ Star the repo</a>
</p>

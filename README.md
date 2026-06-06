<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/license-MIT-emerald?style=for-the-badge" alt="MIT License"/>
  <img src="https://img.shields.io/badge/LLM-Mistral%20Large-FF6F00?style=for-the-badge" alt="Mistral LLM"/>
  <img src="https://img.shields.io/badge/agents-persistent-success?style=for-the-badge" alt="Persistent agents"/>
  <img src="https://img.shields.io/badge/state-JSONL-blue?style=for-the-badge" alt="JSONL persistence"/>
</p>

<h1 align="center">🔬 Emergence Observatory</h1>
<p align="center"><em>An LLM-native multi-agent laboratory for studying emergent intelligence — vocabulary formation, social networks, alliances, cultural persistence, and collective problem-solving through actual natural language conversations.</em></p>

---

## 🧬 What This Is

This is **not** an AGI project. It is **not** an autonomous coding framework.

Emergence Observatory is a scientific instrument for observing **whether** and **how** collective behaviors emerge from a population of autonomous LLM-backed agents. Each agent has a persistent identity, personality, goals, memories, and social relationships. They move through a shared world, gather resources, invent words, form alliances, and communicate in **real natural language** — all driven by a Mistral LLM.

The primary research questions:

| Phenomenon | What We Measure |
|---|---|
| 🗣️ **Vocabulary formation** | Newly invented words, their meanings, adoption rate, survival time |
| 🕸️ **Social network formation** | Relationship graph, affinity scores, community detection |
| 🤝 **Coalition & alliance formation** | Alliance count, duration, mutual resource sharing |
| 📡 **Information propagation** | How news and invented words spread through the population |
| 🏛️ **Cultural persistence** | Longest-surviving invented word, longest alliance |
| 🔧 **Specialization & division of labour** | Action diversity, role distribution, resource specialization |
| 🧩 **Collective problem-solving** | Group vs individual resource gathering efficiency |

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
- **Goals** — 1–2 long-term objectives (e.g., "find rare crystals in the eastern part of the world")
- **Memory** — short-term (last 20 experiences) + episodic (up to 100 consolidated memories)
- **Relationships** — affinity scores for every encountered agent
- **Vocabulary** — learned words + invented words with definitions
- **Alliances** — tracked by ID and alliance name
- **Location** — current position in the world

### The Tick Loop

```
For each tick:
  1. Regenerate world resources
  2. Select N random active agents
  3. For each agent:
     a. Build a rich context prompt (location, nearby agents, memories, goals)
     b. Call Mistral LLM → returns structured JSON decision
     c. Execute the action (move, speak, gather, invent_word, cooperate...)
     d. Persist updated agent state to disk
  4. Compute emergence metrics
  5. Append to JSONL replay log
  6. Push snapshot to live dashboard
```

### Agent Decisions

Agents choose from 11 possible actions, each returned as structured JSON:

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

---

## 🔬 Example Run

After 10 ticks with 8 agents, the LLM (0 failures out of 20 calls) produced:

```
Agent 3 invented "rok"  → "the hard, solid substance found in the ground here"
Agent 1 invented "lumi" → "the dancing light I first saw on the river bank"
Agent 5 invented "zun"  → "the vast empty plain from my memory"
Agent 7 invented "veth" → "the act of moving with purpose across the land"
Agent 2 invented "keth" → "the spark of curiosity or the drive to create meaning"
Agent 0 invented "dren" → "the quiet hum of the world"
```

---

## 🧪 Extensibility

| Direction | How |
|---|---|
| 🧠 **Better memory** | Implement consolidation, decay, or narrative compression in `agent.py` |
| 🌍 **Richer world** | Add dynamic events, seasons, obstacles in `world.py` |
| 🤖 **Different LLM** | Subclass `MistralBridge` for any OpenAI-compatible API |
| 📊 **New metrics** | Add to `MetricsCollector.collect()` |
| 🎭 **Agent heterogeneity** | Vary personality, goals, and capabilities per agent |
| 🔄 **Cultural evolution** | Implement prestige bias, conformity, teaching fidelity |

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

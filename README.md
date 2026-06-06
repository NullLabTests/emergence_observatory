<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/license-MIT-emerald?style=for-the-badge" alt="MIT License"/>
  <img src="https://img.shields.io/badge/agents-1000-important?style=for-the-badge" alt="1000 agents"/>
  <img src="https://img.shields.io/badge/LLM-Mistral%20%7C%20DeepSeek%20%7C%20Ollama-FF6F00?style=for-the-badge" alt="LLM providers"/>
  <img src="https://img.shields.io/badge/codespace-ready-success?style=for-the-badge" alt="Codespace ready"/>
</p>

<h1 align="center">🔬 Emergence Observatory</h1>
<p align="center"><em>Watch intelligence bloom from simple rules — a simulation framework for studying emergent behavior in populations of up to 1000 lightweight AI agents.</em></p>

---

## 🧠 Scientific Motivation

> *"The whole is something besides the parts."* — Aristotle

Emergence — the rise of macro-level patterns from micro-level interactions — sits at the heart of complex systems science. Ant colonies build bridges without architects. Neurons produce thought without a conductor. Markets set prices without central planning.

**Emergence Observatory** gives you a living, instrumented sandbox to watch this process unfold. Every agent follows simple survival rules: move, gather resources, share information. Yet from those local interactions, global patterns arise — shared vocabulary, social networks, collective foraging strategies.

<p align="center">
  <img src="https://img.shields.io/badge/-Communication%20Entropy-8A2BE2?style=flat-square" alt="Communication Entropy"/>
  <img src="https://img.shields.io/badge/-Social%20Graph-00BFFF?style=flat-square" alt="Social Graph"/>
  <img src="https://img.shields.io/badge/-Vocabulary%20Growth-32CD32?style=flat-square" alt="Vocabulary Growth"/>
  <img src="https://img.shields.io/badge/-Strategy%20Propagation-FF8C00?style=flat-square" alt="Strategy Propagation"/>
</p>

### 📊 Four Pillars of Emergence

| Pillar | Question | Metric |
|---|---|---|
| 🗣️ **Communication** | How does local gossip create shared language and information cascades? | Shannon entropy of message types; vocabulary growth curve |
| 🕸️ **Social Structure** | Do agents build stable interaction networks? How does topology shape information flow? | Graph density; degree distribution |
| 🧬 **Strategy Propagation** | Can a successful foraging strategy spread through the population? | Strategy share per tick; adoption latency |
| 🐝 **Collective Intelligence** | Do groups outperform individuals? Is there an optimal population size? | Per-capita energy; resource coverage |

---

## 🏗️ Architecture

```
emergence_observatory/
├── core/                          # Agent, GridWorld, Simulation
│   ├── agent.py                   # Lightweight agent (~1 KB each)
│   ├── grid_world.py              # 2D resource landscape
│   ├── resource.py                # Depletable / regenerating tiles
│   └── simulation.py              # Tick loop orchestration
├── communication/                 # Agent-to-agent messaging
│   ├── message.py
│   └── protocol.py                # Spatial broadcast within range
├── cognition/                     # Rare, routed LLM reasoning
│   ├── novelty_detector.py        # Heuristic: when to invoke the LLM
│   ├── deepseek_bridge.py         # Multi-provider LLM bridge
│   └── cognition_service.py       # Shared throttling & routing
├── metrics/                       # Emergence measurement
│   └── collector.py               # Pluggable metric collection
├── logging/                       # Structured event log (JSONL)
│   └── event_logger.py
├── viz/                           # Live browser dashboard
│   ├── app.py                     # Flask SSE server
│   ├── templates/index.html
│   └── static/viz.js
├── config.py                      # SimulationConfig dataclass
├── run.py                         # CLI entry point
└── experiments/                   # Reproducible experiment scripts
```

### ✨ Design Principles

| # | Principle | Why |
|---|-----------|-----|
| 1 | **Lightweight agents** — plain Python objects, ~1 KB each | 1000 agents fit in a free Codespace |
| 2 | **Local rules** — deterministic & probabilistic decisions | Emergence requires only local interaction |
| 3 | **LLM calls are rare** — novelty-gated, throttled, routed through a shared service | Cost control & realistic bounded rationality |
| 4 | **Multi-provider LLM bridge** — DeepSeek, Mistral, Ollama, any OpenAI-compatible API | No vendor lock-in |
| 5 | **Graceful degradation** — rule-based fallback when API is unavailable | The simulation never crashes |

---

## 🚀 Quick Start

### Installation

```bash
git clone git@github.com:NullLabTests/emergence_observatory.git
cd emergence_observatory
pip install -r requirements.txt
```

### Run the Dashboard

```bash
python run.py --agents 100
```

Open **http://127.0.0.1:5000** — you'll see a live grid of agents moving, gathering, and talking. Metrics update in real time.

### Options

| Flag | Default | Description |
|---|---|---|
| `--agents` | `100` | Number of agents |
| `--width` | `100` | Grid width |
| `--height` | `100` | Grid height |
| `--llm` | off | Enable LLM reasoning |
| `--llm-provider` | `deepseek` | `deepseek`, `mistral`, `ollama`, or `openai-compat` |
| `--llm-model` | *auto* | Model name (e.g. `mistral-large-latest`) |
| `--ollama` | off | Shorthand for Ollama at `localhost:11434` |
| `--tick-interval` | `0.1s` | Seconds between simulation ticks |
| `--port` | `5000` | HTTP port |
| `--max-tick` | `10000` | Stop after this many ticks |

### Headless Experiments

```bash
python experiments/basic_run.py --ticks 500
python experiments/collective_intelligence.py
```

---

## 🤖 LLM Providers

The cognition bridge supports **any** OpenAI-compatible API. Convenience modes for the most common backends:

### DeepSeek API

```bash
export DEEPSEEK_API_KEY="sk-..."
python run.py --llm --llm-provider deepseek
```

### Mistral AI

```bash
export MISTRAL_API_KEY="your-key-here"
python run.py --llm --llm-provider mistral --llm-model mistral-large-latest
```

### Local Ollama

```bash
# First: ollama pull deepseek-r1:8b
python run.py --ollama --llm-model deepseek-r1:8b
```

### Custom Endpoint (vLLM, llama.cpp, etc.)

```bash
python run.py --llm --llm-provider openai-compat \
  --llm-base-url http://localhost:8000/v1 \
  --llm-model my-model
```

When no API is reachable, the bridge falls back to deterministic rules — **your simulation never crashes**.

---

## 🔬 Running at Scale

A 1000-agent, 200-tick test produces measurable emergence:

```
tick   1: agents=1000  energy=99   msgs=0       vocab=0
tick  51: agents=1000  energy=49   msgs=7000    vocab=121
tick 101: agents=995   energy=34   msgs=8150    vocab=126
tick 151: agents=698   energy=22   msgs=8543    vocab=126
tick 200: agents=311   energy=17   msgs=8639    vocab=126

  entropy:      0.486     ← message-type diversity
  graph density: 0.211    ← 21% of possible social edges active
  vocabulary:    126 words ← emergent shared language
```

Resource competition drives interesting extinction dynamics — agents that fail to find food die off, while those that cooperate survive.

---

## 🧪 Extensibility

The framework is designed for future experiments:

| Direction | Hook |
|---|---|
| 🧠 **Memory & culture** | `short_term_memory` / `long_term_memory` ready. Add decay, rehearsal, narrative compression. |
| 👥 **Collective intelligence** | `MetricsCollector.collect()` is pluggable — add custom metrics. |
| 🌍 **Environmental complexity** | Extend `GridWorld` with obstacles, weather, predators, seasons. |
| 🎭 **Agent heterogeneity** | Vary sensor range, speed, memory capacity — study division of labour. |
| 🗺️ **Spatial cognition** | Add cognitive maps, landmark-based navigation, territoriality. |
| 🔄 **Cultural evolution** | Implement imitation, teaching, norm formation, prestige bias. |

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

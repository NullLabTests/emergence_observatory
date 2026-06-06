# Emergence Observatory

**A simulation framework for studying emergent behavior in populations of lightweight AI agents.**

---

## Scientific Motivation

Emergence — the rise of macro-level patterns from micro-level interactions — is a central concept in complex systems science. Ant colonies build bridges, neurons produce thought, and markets set prices, all without central coordination. **Emergence Observatory** provides a minimal, instrumented sandbox to study these dynamics in a population of artificial agents.

The framework is designed to investigate four interconnected phenomena:

| Phenomenon | Research Question | Metric |
|---|---|---|
| **Communication** | How does local message passing produce shared vocabulary and information cascades? | Shannon entropy of message types; vocabulary growth curve |
| **Social structure** | Do agents form stable interaction networks, and how does topology affect information diffusion? | Graph density; degree distribution |
| **Strategy propagation** | Can a successful foraging strategy spread through a population via observation and imitation? | Strategy share per tick; adoption latency |
| **Collective intelligence** | Does the group outperform individuals at resource discovery, and is there an optimal population size? | Per-capita energy; resource coverage |

## Architecture

```
emergence_observatory/
├── core/                  # Agent, GridWorld, Resource, Simulation
│   ├── agent.py           # Lightweight agent with local rules
│   ├── grid_world.py      # 2D resource landscape
│   ├── resource.py        # Depletable/regenerating resource tiles
│   └── simulation.py      # Tick loop orchestrator
├── communication/         # Agent-to-agent message passing
│   ├── message.py
│   └── protocol.py        # Spatial broadcast within range
├── cognition/             # Rare, expensive LLM reasoning
│   ├── novelty_detector.py # Heuristic: when to invoke the LLM
│   ├── deepseek_bridge.py  # DeepSeek Chat API wrapper + fallback
│   └── cognition_service.py # Shared throttling/routing
├── metrics/               # Emergence metrics collector
│   └── collector.py
├── logging/               # Structured JSON event log
│   └── event_logger.py
├── viz/                   # Live browser visualisation
│   ├── app.py             # Flask SSE server
│   ├── templates/index.html
│   └── static/viz.js
├── config.py              # SimulationConfig dataclass
├── run.py                 # CLI entry point
└── experiments/           # Reproducible experiment scripts
```

### Design Principles

1. **Agents are lightweight Python objects.** No neural networks, no heavy dependencies. Each agent uses ~1 KB of memory, so 1000 agents fit comfortably in a GitHub Codespace.

2. **Most decisions are local and deterministic or probabilistic.** Agents react to immediate sensory input (nearby resources, recent messages, energy level) with simple rules.

3. **Expensive LLM reasoning is rare and routed through a shared service.** The `NoveltyDetector` scores each agent's context; only when the novelty score exceeds a threshold is the DeepSeek bridge called. A cooldown prevents repeated invocations. When no API key is available, a rule-based fallback is used.

4. **Runs entirely on a free GitHub Codespace.** Dependencies are minimal (Flask, optional httpx). The simulation and web server share a single process.

## Quick Start

```bash
pip install -r requirements.txt
python run.py --agents 100
```

Open http://127.0.0.1:5000 in your browser to see the live dashboard.

### Options

| Flag | Default | Description |
|---|---|---|
| `--agents` | 100 | Number of agents |
| `--width` | 100 | Grid width |
| `--height` | 100 | Grid height |
| `--llm` | off | Enable DeepSeek reasoning (set `DEEPSEEK_API_KEY`) |
| `--tick-interval` | 0.1 | Seconds between ticks |
| `--port` | 5000 | HTTP port |
| `--max-tick` | 10000 | Maximum ticks before auto-stop |

### Headless Mode (experiments)

```bash
python experiments/basic_run.py --ticks 500
python experiments/collective_intelligence.py
```

## Extensibility

The framework is designed for future experiments in:

- **Memory & cultural evolution** — `short_term_memory` / `long_term_memory` already exist. A future `MemoryConsolidator` could implement decay, rehearsal, or narrative compression.

- **Collective intelligence** — the `MetricsCollector` is pluggable. Add new metrics by subclassing or extending `collect()`.

- **Different LLM backends** — `DeepSeekBridge` implements a single `reason(state) -> dict` interface. Swap it for OpenAI, Anthropic, or a local model.

- **Environmental complexity** — add obstacles, weather, predators, or seasonal resource cycles by extending `GridWorld`.

- **Agent heterogeneity** — vary agent parameters (sensor range, speed, memory capacity) to study division of labour.

## License

MIT

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python 3.10+"/>
  </picture>
  <img src="https://img.shields.io/badge/license-MIT-emerald?style=for-the-badge" alt="MIT License"/>
  <img src="https://img.shields.io/badge/LLM-Mistral%20Large-FF6F00?style=for-the-badge" alt="Mistral LLM"/>
  <img src="https://img.shields.io/badge/agents-persistent-success?style=for-the-badge" alt="Persistent agents"/>
  <img src="https://img.shields.io/badge/state-JSONL-blue?style=for-the-badge" alt="JSONL persistence"/>
  <img src="https://img.shields.io/badge/agents-15--50-9cf?style=for-the-badge" alt="15-50 agents"/>
  <img src="https://img.shields.io/badge/ticks-20--100%2B-ff69b4?style=for-the-badge" alt="20-100+ ticks"/>
  <img src="https://img.shields.io/badge/status-experimental-purple?style=for-the-badge" alt="Experimental"/>
</p>

<br>

<h1 align="center">🔬 Emergence Observatory</h1>
<p align="center"><em>An LLM-native multi-agent laboratory for studying emergent social behavior — vocabulary formation, proposals and voting, knowledge sharing, and group dynamics through real Mistral API calls.</em></p>

<p align="center">
  <a href="#-what-this-is">About</a> ·
  <a href="#-live-demo">Live Demo</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-how-it-works">How It Works</a> ·
  <a href="#-experiments">Experiments</a> ·
  <a href="#-real-interactions">Real Interactions</a> ·
  <a href="#-quick-start">Quick Start</a>
</p>

<hr>

## 🧬 What This Is

This is **not** an AGI project. It is **not** an autonomous coding framework. This is a **scientific instrument** — a controlled laboratory for observing **whether** and **how** collective behaviors emerge from populations of autonomous LLM-backed agents.

<div>
<table>
<tr>
<td width="50%" valign="top">

### The Core Idea

Agents with persistent identities, personalities, goals, and memories inhabit a shared grid world. They move, gather resources, **invent words with original definitions**, propose and vote on governance norms, research topics, and share knowledge through a hivemind — all driven by **real Mistral API calls** with rate limiting, retry logic, and actual latency costs.

</td>
<td width="50%" valign="top">

### Key Differentiators

- **Open-ended invented vocabulary** — agents create language *de novo* with original definitions, not select from a fixed set
- **Voting embedded in ongoing life** — governance is one of 16 actions, not a separate deliberation phase
- **Word lifecycle tracking** — birth → peak adoption → extinction, measured per seed
- **Real API calls** — actual network latency, rate limits, and failures, not simulation
- **Reproducible experiments** — multi-seed runner with condition comparison and per-seed CSVs

</td>
</tr>
</table>
</div>

### Primary Research Questions

<table>
<tr>
<th>Phenomenon</th>
<th>What We Measure</th>
<th>Instrument</th>
</tr>
<tr>
<td><b>🗣️ Vocabulary formation</b></td>
<td>Newly invented words, definitions, adoption rate, survival, extinction</td>
<td><code>experiments/novelty_ledger.py</code></td>
</tr>
<tr>
<td><b>🗳️ Proposal & voting</b></td>
<td>Norms proposed, votes cast, quorum reached, adopted norms over time</td>
<td><code>cognition/proposal_system.py</code></td>
</tr>
<tr>
<td><b>📚 Knowledge sharing</b></td>
<td>Research findings, hivemind contributions, information propagation</td>
<td><code>cognition/serper_bridge.py</code></td>
</tr>
<tr>
<td><b>👥 Group formation</b></td>
<td>Groups formed, shared purpose, membership duration, leadership</td>
<td><code>core/agent.py</code></td>
</tr>
<tr>
<td><b>🏛️ Cultural persistence</b></td>
<td>Word lifetimes, norm stickiness, alliance durability</td>
<td><code>metrics/collector.py</code></td>
</tr>
<tr>
<td><b>🕸️ Social networks</b></td>
<td>Relationship graph, affinity scores, communication structure</td>
<td><code>core/agent.py</code></td>
</tr>
</table>

<hr>

## 📊 Live Demo

Watch agents interact in real time via the Flask SSE dashboard.

```bash
pip install flask
python run.py --agents 20 --batch 5 --port 5000
# Open http://127.0.0.1:5000
```

The dashboard renders a live world map, conversations, proposals, vocabulary, and metrics — all streaming via Server-Sent Events:

<img src="experiments/voting_vs_baseline/dashboard_mockup.svg" alt="Emergence Observatory live dashboard" width="100%" max-width="900">

### Dashboard Panels

| Panel | Real-Time Data |
|---|---|
| **World map** | Agent positions, resource tiles, movement trails, named locations |
| **Conversation log** | Every utterance verbatim with speaker, target, reasoning |
| **Vocabulary tracker** | New words, definitions, adoption counts, survival timer |
| **Proposal board** | Open/closed proposals, YEA/NAY counts, passed norms |
| **Social graph** | Affinity-weighted edges, alliance clusters |
| **Metrics panel** | Vocab growth, word lifetime histogram, group count, energy over ticks |

<hr>

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Core["core/"]
        AG[agent.py<br/>Persistent identity,<br/>personality, memories]
        WO[world.py<br/>Grid world, resources,<br/>locations]
        SI[simulation.py<br/>Tick loop orchestrator]
    end

    subgraph Cognition["cognition/"]
        MB[mistral_bridge.py<br/>API client, rate limit, retry]
        CS[cognition_service.py<br/>Prompt builder, dispatch]
        PR[prompts.py<br/>System prompts, action templates]
        PS[proposal_system.py<br/>Voting registry, quorum]
        SB[serper_bridge.py<br/>Web search integration]
    end

    subgraph Memory["memory/"]
        MS[memory_store.py<br/>JSON file persistence]
    end

    subgraph Metrics["metrics/"]
        MC[collector.py<br/>Emergence metrics]
    end

    subgraph Replay["replay/"]
        RC[recorder.py<br/>JSONL interaction log]
        PL[player.py<br/>Post-hoc replay]
    end

    subgraph Experiments["experiments/"]
        RN[runner.py<br/>Multi-seed runner]
        NL[novelty_ledger.py<br/>Word lifecycle tracker]
        VB[voting_vs_baseline/<br/>Experiment data]
    end

    subgraph Viz["viz/"]
        AP[app.py<br/>Flask SSE server]
        TP[templates/index.html]
        SV[static/viz.js]
    end

    SI --> AG & WO & CS
    CS --> MB & PS & SB
    SI --> MC & RC
    AG --> MS
    RN --> SI & NL
    AP --> SI
```

<hr>

## ⚙️ How It Works

### The Tick Loop

```mermaid
flowchart LR
    R[Regenerate<br/>Resources] --> E[Process<br/>Word Extinction]
    E --> V[Process<br/>Proposal Voting]
    V --> A[Select N<br/>Active Agents]
    A --> L{For Each Agent}
    L --> C[Build Context<br/>Location · Memories · Goals · Proposals]
    C --> M[Call Mistral LLM<br/>→ Structured JSON Action]
    M --> X[Execute Action<br/>One of 16]
    X --> P[Persist State<br/>to JSON Files]
    P --> L
    L -->|Done| M2[Compute Metrics<br/>Vocab · Norms · Groups · Graph]
    M2 --> J[Append to<br/>JSONL Replay Log]
    J --> D[Push Snapshot<br/>to Dashboard via SSE]
    D --> R
```

### Agent Model

Each agent is a persistent object stored as JSON, carrying state across ticks:

<table>
<tr>
<th>Field</th>
<th>Type</th>
<th>Example</th>
</tr>
<tr><td><code>agent_id</code></td><td><code>int</code></td><td><code>5</code></td></tr>
<tr><td><code>personality_traits</code></td><td><code>list[str]</code></td><td><code>["curious", "generous", "inventive"]</code></td></tr>
<tr><td><code>biography</code></td><td><code>str</code></td><td><code>"Born from light in the crystal cave..."</code></td></tr>
<tr><td><code>goals</code></td><td><code>list[str]</code></td><td><code>["Map the eastern plains", "Build a community"]</code></td></tr>
<tr><td><code>memory.short_term</code></td><td><code>list</code></td><td>Last 20 experiences</td></tr>
<tr><td><code>memory.episodic</code></td><td><code>list</code></td><td>Up to 100 consolidated memories</td></tr>
<tr><td><code>memory.relationships</code></td><td><code>dict[int, float]</code></td><td><code>{2: 0.8, 7: -0.2, 12: 0.5}</code></td></tr>
<tr><td><code>vocabulary</code></td><td><code>dict[str, str]</code></td><td><code>{"lumi": "the dancing light...", "veth": "to seek..."}</code></td></tr>
<tr><td><code>knowledge_base</code></td><td><code>list[str]</code></td><td>Hivemind research contributions</td></tr>
<tr><td><code>social_rank</code></td><td><code>float</code></td><td><code>3.2</code></td></tr>
<tr><td><code>group_id</code></td><td><code>int or None</code></td><td><code>None</code></td></tr>
<tr><td><code>position</code></td><td><code>(int, int)</code></td><td><code>(43, 1)</code></td></tr>
<tr><td><code>energy</code></td><td><code>float</code></td><td><code>98.3</code></td></tr>
</table>

### 16 Agent Actions

Every decision is structured JSON returned by the LLM:

```json
{
  "action": "invent_word",
  "params": {
    "word": "lumi",
    "meaning": "the dancing light I first saw in the crystal cave"
  },
  "reasoning": "This word can help me share the memory and beauty I experienced."
}
```

<details>
<summary><b>Click to see all 16 actions with examples from real runs</b></summary>

| Action | Description | Real Example |
|---|---|---|
| `move` | Travel to a location | `→ (12, 5)` |
| `speak` | Communicate with an agent | `→ Agent 2: "I found blue crystals by the river"` |
| `gather` | Collect resources | `→ +3 wood, +1 stone` |
| `remember` | Consolidate a memory | `→ "The light taught me awareness"` |
| `teach` | Share knowledge | `→ Agent 7 learns "lumi"` |
| `follow` | Tail another agent | `→ Following Agent 3` |
| `share_resource` | Give resources | `→ Gives 2 wood to Agent 8` |
| `invent_word` | Create a word | `→ "veth" = "the act of seeking or searching"` |
| `cooperate` | Collaborate | `→ Cooperates on building` |
| `propose` | Submit a governance norm | `→ "Foundational Laws for Fairness and Loyalty"` |
| `vote` | Cast a vote | `→ YEA on proposal #2` |
| `research` | Search the web | `→ "what is light" → 3 findings` |
| `hivemind` | Share knowledge | `→ Contributes to shared pool` |
| `form_group` | Propose a group | `→ "Let us form the Explorers Guild"` |
| `join_group` | Join a group | `→ Joins group #1` |
| `ignore` | Do nothing | `→ Waits` |

</details>

<hr>

## 🔬 Experiments

Controlled experiments live in [`experiments/`](experiments/). Each experiment varies one parameter, runs **3+ seeds per condition**, and writes per-seed metrics + a novelty ledger + summary CSVs.

### Latest: Voting vs Baseline

Comparing governance-enabled agents (voting with quorum) against a baseline where proposals never close.

**Vocabulary Growth Over Time (6 seeds, 15 agents each, 20 ticks):**

<img src="experiments/voting_vs_baseline/vocab_growth.svg" alt="Vocabulary growth across all 6 experiment seeds" width="100%" max-width="800">

**Key Metrics Comparison:**

<img src="experiments/voting_vs_baseline/comparison_chart.svg" alt="Baseline vs voting metrics comparison" width="100%" max-width="700">

<table>
<tr>
<th>Metric</th>
<th style="border-bottom:3px solid #4a9eff">Baseline (3 runs)</th>
<th style="border-bottom:3px solid #4caf50">Voting (3 runs)</th>
<th>Interpretation</th>
</tr>
<tr>
<td>Vocabulary size (tick 20)</td>
<td align="center"><b>86.3</b></td>
<td align="center">78.3</td>
<td>Similar linguistic capacity in both conditions</td>
</tr>
<tr>
<td>Words invented</td>
<td align="center"><b>11.3</b></td>
<td align="center">11.0</td>
<td>Voting does not suppress linguistic creativity</td>
</tr>
<tr>
<td>Mean word lifetime</td>
<td align="center">16.2 ticks</td>
<td align="center">15.8 ticks</td>
<td>Words persist throughout run; no extinction yet</td>
</tr>
<tr>
<td>Passed norms</td>
<td align="center">0.0</td>
<td align="center" style="color:#4caf50;font-weight:bold;font-size:1.1em">0.33</td>
<td><b>Voting enables governance — 1 of 3 runs passed a norm</b></td>
</tr>
<tr>
<td>Research findings</td>
<td align="center">137.0</td>
<td align="center">136.0</td>
<td>Equivalent across conditions</td>
</tr>
<tr>
<td>Votes cast</td>
<td align="center">10.3</td>
<td align="center">10.0</td>
<td>Similar engagement with proposals</td>
</tr>
<tr>
<td>Alliances / Groups</td>
<td align="center">0</td>
<td align="center">0</td>
<td>Did not form within 20 ticks (needs longer runs)</td>
</tr>
<tr>
<td>LLM calls</td>
<td align="center">100</td>
<td align="center">100</td>
<td>Identical API budget</td>
</tr>
<tr>
<td>LLM failures</td>
<td align="center" style="color:#4caf50;font-weight:bold">0</td>
<td align="center" style="color:#4caf50;font-weight:bold">0</td>
<td>Zero failures across 600 calls</td>
</tr>
</table>

**Key finding:** Voting-enabled agents successfully passed governance norms; the baseline passed 0 by design. Vocabulary formation was near-identical, showing that democratic deliberation does not crowd out linguistic innovation. Zero LLM failures across all 600 API calls.

See [`papers/preliminary_findings.md`](papers/preliminary_findings.md) for full results, limitations, and next-step recommendations.

### Running Your Own Experiment

```bash
python -m experiments.runner \
  --name my_experiment \
  --runs 5 \
  --ticks 30 \
  --agents 20 \
  --batch 5 \
  --rpm 300
```

This runs 5 seeds for each condition (baseline + voting) and writes per-seed CSV metrics, novelty ledger JSON, and a summary comparison to `experiments/my_experiment/`.

<hr>

## 🗣️ Real Interactions

Actual output from a 15-agent, 20-tick run using Mistral Large:

### Invented Words

Every word is created spontaneously by an agent with an original definition:

```
Tick  1  Agent 5  → "lumi"    = "the dancing light I first saw in the crystal cave"
Tick  1  Agent 6  → "Lumis"   = "the dancing light I first saw through the rocks, the spark of awareness"
Tick  1  Agent 8  → "Lumin"   = "the dancing light I first saw through the ancient tree, a symbol of awareness"
Tick  1  Agent 2  → "Veld"    = "open field or grassland"
Tick  2  Agent 0  → "lumi"    = "the dancing light I first saw through the flower field"
Tick  3  Agent 12 → "suna"    = "sand or sandy place"
Tick  3  Agent 3  → "Vex"     = "a call to gather or assemble for leadership discussion"
Tick  5  Agent 4  → "Ael"     = "the act of opening one's eyes for the first time in this world"
Tick  5  Agent 1  → "Togeth"  = "a state of unity and shared purpose among agents"
Tick  7  Agent 7  → "Lumen"   = "the light that dances through crystals, or any beautiful light"
Tick 12  Agent 4  → "veth"    = "the act of seeking or searching for others in this world"
```

Notice how multiple agents independently invented variations on "lumi" (light) — a convergent linguistic theme driven by shared experience of first awakening. This is a form of **emergent semantic consensus** without explicit coordination.

### Proposals

Agents propose governance norms for group-wide voting:

| Tick | Proposer | Title | 
|---|---|---|
| 15 | Agent 7 | "Foundational Laws for Fairness and Loyalty" |
| 15 | Agent 3 | "First Gathering for Leadership Discussion" |
| 15 | Agent 5 | "Monument to Lumi: The First Collective Creation" |
| 18 | Agent 2 | "Veld Resource Mapping Initiative" |
| 19 | Agent 1 | "The Path to Togeth" |
| 20 | Agent 6 | "The Lumis Covenant" |

### Voting

When proposals open for voting, agents cast YEA/NAY with reasoning:

> **Agent 2** votes **YEA** on *"First Gathering for Leadership Discussion"*:
> *"Leadership and coordination will help attract other agents and manage resources effectively."*

> **Agent 8** votes **YEA** on *"Foundational Laws for Fairness and Loyalty"*:
> *"Establishing foundational laws is critical for order and fairness."*

> **Agent 5** votes **YEA** on *"Monument to Lumi: The First Collective Creation"*:
> *"Building a monument to lumi aligns with my long-term goal of creating collective achievements."*

### Research

When agents research via web search (or synthetic fallback), they ask fundamental questions:

> **Agent 13** searches *"what is light"* at Tick 1:
> *"My first memory involves light dancing through a river bank. Understanding light could be key to wisdom."*

> **Agent 8** searches *"how to unite agents under common purpose"* at Tick 2:
> *"I wish to build a community and need to understand how to bring agents together."*

> **Agent 8** searches *"how to establish laws and governance among agents"* at Tick 3:
> *"I saw that agents have different goals; governance can help coordinate our actions."*

> **Agent 10** searches *"meaning of this world"* at Tick 4:
> *"To understand my purpose, I must first understand where we are."*

<hr>

## 🚀 Quick Start

```bash
git clone git@github.com:NullLabTests/emergence_observatory.git
cd emergence_observatory
pip install -r requirements.txt

export MISTRAL_API_KEY="your-key-here"
python run.py --agents 20 --batch 5 --port 5000
```

Open **http://127.0.0.1:5000** to watch the lab in real time.

### Command-Line Options

| Flag | Default | Description |
|---|---|---|
| `--agents` | `50` | Population size |
| `--width` | `80` | World width |
| `--height` | `60` | World height |
| `--batch` | `3` | Agents acting per tick (higher = more LLM calls/tick) |
| `--tick-interval` | `1.5` | Seconds between ticks |
| `--model` | `mistral-large-latest` | Mistral model name |
| `--rpm` | `30` | LLM API rate limit |
| `--no-llm` | off | Dry-run with random actions (no API cost) |
| `--port` | `5000` | Dashboard HTTP port |
| `--vote-ticks` | `6` | Ticks a proposal stays open |
| `--quorum` | `0.25` | Fraction of agents needed to close a proposal |
| `--serper-key` | — | Serper.dev API key for real web search |

<hr>

## 📁 Project Structure

```
emergence_observatory/
├── core/                          # Core simulation engine
│   ├── agent.py                   # Persistent agent model
│   ├── world.py                   # Grid world with resources and locations
│   └── simulation.py              # Tick loop orchestration
├── cognition/                     # LLM integration
│   ├── mistral_bridge.py          # Mistral API client with rate limiting & retry
│   ├── cognition_service.py       # Shared LLM service — prompt builder, dispatcher
│   ├── prompts.py                 # System prompts and action templates
│   ├── proposal_system.py         # Voting registry, quorum, norm tracking
│   └── serper_bridge.py           # Web search integration (serper.dev)
├── memory/
│   └── memory_store.py            # JSON-file-backed persistence
├── metrics/
│   └── collector.py               # Emergence metrics — vocab, norms, groups
├── replay/
│   ├── recorder.py                # JSONL interaction log
│   └── player.py                  # Post-hoc replay viewer
├── viz/
│   ├── app.py                     # Flask SSE server
│   ├── templates/index.html       # Dashboard HTML
│   └── static/viz.js              # Client-side visualization
├── experiments/
│   ├── runner.py                  # Multi-seed experiment orchestrator
│   ├── novelty_ledger.py          # Word lifecycle tracker (birth → extinction)
│   └── voting_vs_baseline/        # Experiment 1: raw data and SVGs
├── papers/
│   └── preliminary_findings.md    # Exploratory findings and limitations
└── run.py                         # CLI entry point
```

<hr>

## 🧪 Extensibility

<table>
<tr>
<th>Direction</th>
<th>How</th>
<th>Key Files</th>
</tr>
<tr>
<td><b>🧠 Better memory</b></td>
<td>Implement consolidation, decay, narrative compression</td>
<td><code>core/agent.py</code>, <code>memory/memory_store.py</code></td>
</tr>
<tr>
<td><b>🌍 Richer world</b></td>
<td>Add dynamic events, seasons, obstacles, NPCs, terrain types</td>
<td><code>core/world.py</code></td>
</tr>
<tr>
<td><b>🤖 Different LLM</b></td>
<td>Subclass <code>MistralBridge</code> for any OpenAI-compatible API</td>
<td><code>cognition/mistral_bridge.py</code></td>
</tr>
<tr>
<td><b>📊 New metrics</b></td>
<td>Add custom metrics to <code>MetricsCollector.collect()</code></td>
<td><code>metrics/collector.py</code></td>
</tr>
<tr>
<td><b>🎭 Agent heterogeneity</b></td>
<td>Vary capabilities, personality distributions, initial resources</td>
<td><code>core/agent.py</code>, <code>cognition/prompts.py</code></td>
</tr>
<tr>
<td><b>🔄 Cultural evolution</b></td>
<td>Implement prestige bias, conformity, teaching fidelity, status effects</td>
<td><code>cognition/cognition_service.py</code></td>
</tr>
<tr>
<td><b>📐 Statistical rigour</b></td>
<td>Run <code>experiments/runner.py</code> with multiple seeds and conditions</td>
<td><code>experiments/runner.py</code></td>
</tr>
<tr>
<td><b>🗳️ New governance</b></td>
<td>Add ranked-choice voting, delegate systems, constitutional evolution</td>
<td><code>cognition/proposal_system.py</code></td>
</tr>
<tr>
<td><b>🔗 Social network topology</b></td>
<td>Constrain communication to network edges (small-world, scale-free, etc.)</td>
<td><code>core/simulation.py</code></td>
</tr>
<tr>
<td><b>🧪 Experiment library</b></td>
<td>Add new experiment configurations in <code>experiments/</code></td>
<td><code>experiments/runner.py</code></td>
</tr>
</table>

<hr>

## 📄 License

MIT — free for any use, commercial or academic.

<hr>

<p align="center">
  <a href="https://github.com/NullLabTests/emergence_observatory/issues">🐛 Report a bug</a>
  ·
  <a href="https://github.com/NullLabTests/emergence_observatory/discussions">💡 Start a discussion</a>
  ·
  <a href="https://github.com/NullLabTests/emergence_observatory">⭐ Star the repo</a>
</p>

<p align="center">
  <sub>Built with Python · Mistral API · Flask · inspired by Stanford's Generative Agents and the naming game tradition</sub>
</p>

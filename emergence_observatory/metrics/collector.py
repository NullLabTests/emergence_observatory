from __future__ import annotations
import math
from collections import Counter, defaultdict


class MetricsCollector:
    """Collects and exposes emergence metrics each tick.

    Metrics computed:

      - **Communication entropy**  — Shannon entropy of message-type distribution.
      - **Social graph density**   — ratio of active edges to possible edges.
      - **Vocabulary growth**      — unique words in the collective vocabulary.
      - **Strategy propagation**   — how the dominant strategy share changes.
    """

    def __init__(self):
        self.history: dict[str, list] = {
            "entropy": [],
            "graph_density": [],
            "vocab_size": [],
            "strategy_distribution": [],
            "num_agents": [],
            "avg_energy": [],
        }

    def collect(self, simulation) -> None:
        agents = list(simulation.agents.values())
        n = len(agents)
        self.history["num_agents"].append(n)

        if n == 0:
            return

        # --- Communication entropy -------------------------------------------------
        msg_types = Counter()
        for a in agents:
            for m in a.message_history:
                msg_types[m.get("msg_type", "broadcast")] += 1
        total_msgs = sum(msg_types.values())
        entropy = 0.0
        if total_msgs > 0:
            for count in msg_types.values():
                p = count / total_msgs
                if p > 0:
                    entropy -= p * math.log2(p)
        self.history["entropy"].append(entropy)

        # --- Social graph density --------------------------------------------------
        edges = sum(len(a.social_links) for a in agents)
        possible = n * (n - 1)
        density = edges / possible if possible > 0 else 0.0
        self.history["graph_density"].append(density)

        # --- Collective vocabulary -------------------------------------------------
        all_words: set[str] = set()
        for a in agents:
            all_words.update(a.vocabulary)
        self.history["vocab_size"].append(len(all_words))

        # --- Strategy distribution -------------------------------------------------
        strat_counter: dict[str, int] = Counter(a.strategy for a in agents)
        self.history["strategy_distribution"].append(dict(strat_counter))

        # --- Average energy --------------------------------------------------------
        avg_e = sum(a.energy for a in agents) / n
        self.history["avg_energy"].append(avg_e)

    def current(self) -> dict:
        """Return the *latest* values as a flat dictionary."""
        if not self.history["num_agents"]:
            return {}
        idx = -1
        return {
            "entropy": round(self.history["entropy"][idx], 3) if self.history["entropy"] else 0.0,
            "graph_density": round(self.history["graph_density"][idx], 5) if self.history["graph_density"] else 0.0,
            "vocab_size": self.history["vocab_size"][idx] if self.history["vocab_size"] else 0,
            "strategy_distribution": self.history["strategy_distribution"][idx] if self.history["strategy_distribution"] else {},
            "num_agents": self.history["num_agents"][idx] if self.history["num_agents"] else 0,
            "avg_energy": round(self.history["avg_energy"][idx], 1) if self.history["avg_energy"] else 0.0,
        }

    def full_history(self) -> dict:
        return dict(self.history)

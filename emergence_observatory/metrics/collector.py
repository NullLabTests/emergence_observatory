from __future__ import annotations
import math
import json
from collections import Counter, defaultdict
from pathlib import Path


class MetricsCollector:
    """Continuously computed emergence metrics.

    Written to `{base_path}/metrics.jsonl` every tick.
    """

    def __init__(self, base_path: str = "data/metrics"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)
        self._history: dict[str, list] = {
            "tick": [],
            "vocab_size": [],
            "message_entropy": [],
            "graph_density": [],
            "num_communities": [],
            "num_alliances": [],
            "longest_word_survival": [],
            "longest_alliance_survival": [],
            "avg_energy": [],
            "num_agents": [],
            "action_counts": [],
        }
        self._word_births: dict[str, int] = {}
        self._alliance_births: dict[str, int] = {}

    def collect(self, simulation) -> dict:
        agents = list(simulation.agents.values())
        n = len(agents)
        t = simulation.tick

        self._history["tick"].append(t)
        self._history["num_agents"].append(n)

        if n == 0:
            return self.current()

        # --- Collective vocabulary ---
        all_vocab: set[str] = set()
        for a in agents:
            all_vocab.update(a.vocabulary)
        self._history["vocab_size"].append(len(all_vocab))

        # --- Message entropy ---
        msg_types: Counter[str] = Counter()
        for a in agents:
            for m in a.conversation_history:
                pass
        convos = simulation.conversation_log
        for c in convos:
            msg_types["speak"] += 1
        total_msgs = sum(msg_types.values())
        entropy = 0.0
        if total_msgs > 0:
            for count in msg_types.values():
                p = count / total_msgs
                if p > 0:
                    entropy -= p * math.log2(p)
        self._history["message_entropy"].append(entropy)

        # --- Social graph density ---
        edges = sum(len(a.relationship_memory) for a in agents)
        possible = n * (n - 1)
        density = edges / possible if possible > 0 else 0.0
        self._history["graph_density"].append(density)

        # --- Alliances ---
        all_alliances: set[str] = set()
        for a in agents:
            for k, v in a.alliances.items():
                all_alliances.add(v)
        self._history["num_alliances"].append(len(all_alliances))

        # --- Communities (simple: agents with mutual relationships) ---
        communities = self._detect_communities(agents)
        self._history["num_communities"].append(communities)

        # --- Invented word survival ---
        all_invented: dict[str, int] = {}
        for a in agents:
            for w in a.invented_words:
                all_invented[w] = all_invented.get(w, 0) + 1
        for w in all_invented:
            if w not in self._word_births:
                self._word_births[w] = t
        survival = 0
        for w, bt in self._word_births.items():
            if w in all_invented:
                survival = max(survival, t - bt)
        self._history["longest_word_survival"].append(survival)

        # --- Alliance survival ---
        active_alls = set()
        for a in agents:
            for k, v in a.alliances.items():
                active_alls.add(v)
        for al in active_alls:
            if al not in self._alliance_births:
                self._alliance_births[al] = t
        al_survival = 0
        for al, bt in self._alliance_births.items():
            if al in active_alls:
                al_survival = max(al_survival, t - bt)
        self._history["longest_alliance_survival"].append(al_survival)

        # --- Avg energy ---
        avg_e = sum(a.energy for a in agents) / n
        self._history["avg_energy"].append(avg_e)

        # --- Action counts ---
        counts: Counter[str] = Counter()
        for a in agents:
            pass
        self._history["action_counts"].append(dict(counts))

        # Write to disk
        self._write_metrics(t)

        return self.current()

    def _detect_communities(self, agents) -> int:
        # Greedy connected-components on relationship graph
        adj: dict[int, set[int]] = defaultdict(set)
        for a in agents:
            for peer in a.relationship_memory:
                adj[a.agent_id].add(peer)
                adj[peer].add(a.agent_id)

        visited: set[int] = set()
        components = 0
        for aid in adj:
            if aid not in visited:
                components += 1
                stack = [aid]
                while stack:
                    cur = stack.pop()
                    if cur not in visited:
                        visited.add(cur)
                        stack.extend(adj[cur] - visited)
        return components

    def _write_metrics(self, tick: int) -> None:
        m = self.current()
        m["tick"] = tick
        path = self.base / "metrics.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps(m, default=str) + "\n")

    def current(self) -> dict:
        if not self._history["tick"]:
            return {}
        i = -1
        return {
            "vocab_size": self._history["vocab_size"][i] if self._history["vocab_size"] else 0,
            "message_entropy": round(self._history["message_entropy"][i], 3) if self._history["message_entropy"] else 0.0,
            "graph_density": round(self._history["graph_density"][i], 5) if self._history["graph_density"] else 0.0,
            "num_communities": self._history["num_communities"][i] if self._history["num_communities"] else 0,
            "num_alliances": self._history["num_alliances"][i] if self._history["num_alliances"] else 0,
            "longest_word_survival": self._history["longest_word_survival"][i] if self._history["longest_word_survival"] else 0,
            "longest_alliance_survival": self._history["longest_alliance_survival"][i] if self._history["longest_alliance_survival"] else 0,
            "avg_energy": round(self._history["avg_energy"][i], 1) if self._history["avg_energy"] else 0.0,
            "num_agents": self._history["num_agents"][i] if self._history["num_agents"] else 0,
        }

    def full_history(self) -> dict:
        return dict(self._history)

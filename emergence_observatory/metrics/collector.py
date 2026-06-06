from __future__ import annotations
import math
import json
from collections import Counter, defaultdict
from pathlib import Path


class MetricsCollector:
    """Continuously computed emergence metrics, written to disk."""

    def __init__(self, base_path: str = "data/metrics"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)
        self._history: dict[str, list] = {
            "tick": [],
            "vocab_size": [], "message_entropy": [],
            "graph_density": [], "num_communities": [],
            "num_alliances": [], "num_groups": [],
            "longest_word_survival": [], "longest_alliance_survival": [],
            "avg_energy": [], "num_agents": [],
            "open_proposals": [], "passed_norms": [],
            "knowledge_topics": [], "total_research": [],
            "total_votes": [], "total_proposals_made": [],
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

        all_vocab: set[str] = set()
        for a in agents:
            all_vocab.update(a.vocabulary)
        self._history["vocab_size"].append(len(all_vocab))

        convos = simulation.conversation_log
        total_msgs = len(convos)
        entropy = 0.0
        if total_msgs > 0:
            p = 1.0
            entropy = 0.0
        self._history["message_entropy"].append(entropy if total_msgs > 0 else 0.0)

        edges = sum(len(a.relationship_memory) for a in agents)
        possible = n * (n - 1)
        density = edges / possible if possible > 0 else 0.0
        self._history["graph_density"].append(density)

        all_alliances: set[str] = set()
        for a in agents:
            for k, v in a.alliances.items():
                all_alliances.add(v)
        self._history["num_alliances"].append(len(all_alliances))

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
        self._history["num_communities"].append(components)

        all_invented: dict[str, int] = {}
        for a in agents:
            for w in a.invented_words:
                all_invented[w] = all_invented.get(w, 0) + 1
        for w in all_invented:
            if w not in self._word_births:
                self._word_births[w] = t
        survival = max((t - bt for w, bt in self._word_births.items() if w in all_invented), default=0)
        self._history["longest_word_survival"].append(survival)

        active_alls = set()
        for a in agents:
            for k, v in a.alliances.items():
                active_alls.add(v)
        for al in active_alls:
            if al not in self._alliance_births:
                self._alliance_births[al] = t
        al_survival = max((t - bt for al, bt in self._alliance_births.items() if al in active_alls), default=0)
        self._history["longest_alliance_survival"].append(al_survival)

        avg_e = sum(a.energy for a in agents) / n
        self._history["avg_energy"].append(avg_e)

        props = getattr(simulation.world, "proposals", None)
        if props:
            self._history["open_proposals"].append(len(props.open_proposals()))
            self._history["passed_norms"].append(len(props.norms))
        else:
            self._history["open_proposals"].append(0)
            self._history["passed_norms"].append(0)

        ktopics = len(getattr(simulation.world, "knowledge_repo", {}))
        self._history["knowledge_topics"].append(ktopics)

        total_research = sum(len(a.research_findings) for a in agents)
        self._history["total_research"].append(total_research)

        total_votes = sum(a.votes_cast for a in agents)
        self._history["total_votes"].append(total_votes)

        total_props = sum(a.proposals_made for a in agents)
        self._history["total_proposals_made"].append(total_props)

        num_groups = len(getattr(simulation.world, "groups", {}))
        self._history["num_groups"].append(num_groups)

        self._write_metrics(t)
        return self.current()

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
            k: (self._history[k][i] if self._history[k] else 0)
            for k in ("vocab_size", "message_entropy", "graph_density",
                      "num_communities", "num_alliances", "num_groups",
                      "longest_word_survival", "longest_alliance_survival",
                      "avg_energy", "num_agents",
                      "open_proposals", "passed_norms",
                      "knowledge_topics", "total_research",
                      "total_votes", "total_proposals_made")
        }

    def full_history(self) -> dict:
        return dict(self._history)

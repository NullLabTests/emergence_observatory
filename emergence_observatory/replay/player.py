from __future__ import annotations
import json
from pathlib import Path
from typing import Iterator


class Player:
    """Replay a recorded simulation run.

    Reads the JSONL file and yields events in order.
    """

    def __init__(self, path: str):
        self.path = Path(path)

    def events(self) -> Iterator[dict]:
        if not self.path.exists():
            return
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def filter_agent(self, agent_id: int) -> Iterator[dict]:
        for e in self.events():
            if e.get("agent_id") == agent_id:
                yield e

    def summary(self) -> dict:
        ticks = set()
        agents = set()
        actions = {}
        for e in self.events():
            ticks.add(e.get("tick"))
            agents.add(e.get("agent_id"))
            a = e.get("action", "?")
            actions[a] = actions.get(a, 0) + 1

        return {
            "total_events": sum(1 for _ in self.events()),
            "unique_ticks": len(ticks),
            "unique_agents": len(agents),
            "action_counts": actions,
        }

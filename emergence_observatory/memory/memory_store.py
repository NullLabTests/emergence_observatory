from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional


class MemoryStore:
    """JSON-file-backed persistence for agent and world state.

    Each agent is stored as ``{memory_path}/agent_{id}.json``.
    World state is ``{memory_path}/world.json``.
    """

    def __init__(self, base_path: str = "data/memory"):
        self._root = Path(base_path)
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Agent persistence
    # ------------------------------------------------------------------

    def save_agent(self, agent_id: int, data: dict) -> None:
        path = self._root / f"agent_{agent_id}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_agent(self, agent_id: int) -> Optional[dict]:
        path = self._root / f"agent_{agent_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def delete_agent(self, agent_id: int) -> None:
        path = self._root / f"agent_{agent_id}.json"
        path.unlink(missing_ok=True)

    def list_agents(self) -> list[int]:
        ids = []
        for p in self._root.glob("agent_*.json"):
            try:
                ids.append(int(p.stem.split("_")[1]))
            except (IndexError, ValueError):
                pass
        return sorted(ids)

    # ------------------------------------------------------------------
    # World persistence
    # ------------------------------------------------------------------

    def save_world(self, data: dict) -> None:
        path = self._root / "world.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_world(self) -> Optional[dict]:
        path = self._root / "world.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Tick / snapshot
    # ------------------------------------------------------------------

    def save_tick(self, tick: int, data: dict) -> None:
        path = self._root / f"tick_{tick:06d}.json"
        with open(path, "w") as f:
            json.dump(data, f, default=str)

    def clear(self) -> None:
        for p in self._root.glob("*"):
            p.unlink()

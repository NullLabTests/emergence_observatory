from __future__ import annotations
import random
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentSnapshot:
    agent_id: int
    x: int
    y: int
    energy: float
    inventory_size: int
    vocabulary_size: int
    strategy: str
    last_action: str


class Agent:
    """A lightweight AI agent in the grid world.

    Agents act via local deterministic / probabilistic rules.  Expensive LLM
    calls are *not* made here — they flow through the shared CognitionService.
    """

    def __init__(self, agent_id: int, x: int, y: int, config):
        self.id = agent_id
        self.position: tuple[int, int] = (x, y)
        self.energy = config.initial_energy
        self.inventory: dict[str, float] = {}
        self.short_term_memory: list[dict] = []
        self.long_term_memory: list[dict] = []
        self.vocabulary: set[str] = set()

        self.config = config
        self.last_action: str = "idle"
        self.strategy: str = "explore"
        self.known_resource_spots: list[tuple[int, int]] = []
        self.social_links: dict[int, float] = {}
        self.message_history: list[dict] = []
        self.tick_count: int = 0
        self.ticks_since_llm: int = 999

    # ------------------------------------------------------------------
    # Per-step decision
    # ------------------------------------------------------------------

    def step(self, grid_world, comm_system) -> dict:
        self.tick_count += 1
        self.ticks_since_llm += 1

        self._scan_nearby_resources(grid_world)

        if self.energy < 40.0:
            log = self._seek_resources(grid_world)
        elif self.tick_count % 7 == 0 and self.energy > 50.0:
            log = self._try_communicate(comm_system)
        elif random.random() < 0.20:
            log = self._explore(grid_world)
        else:
            log = self._move_random(grid_world)

        self.last_action = log.get("action", "idle")
        self.energy -= self.config.energy_cost_per_move
        if self.energy < 0.0:
            self.energy = 0.0

        self._maybe_consolidate_memory()
        return log

    # ------------------------------------------------------------------
    # Behaviours
    # ------------------------------------------------------------------

    def _seek_resources(self, grid_world) -> dict:
        res_here = grid_world.resources_at(self.position)
        if res_here:
            gathered = {}
            for tile in res_here:
                qty = tile.gather(5.0)
                gathered[tile.resource_type] = gathered.get(tile.resource_type, 0) + qty
                self.energy += self.config.energy_gain_per_resource * (qty / 5.0)
            for k, v in gathered.items():
                self.inventory[k] = self.inventory.get(k, 0) + v
            return {"action": "gather", "resources": gathered}

        target = self._nearest_resource(grid_world, radius=6)
        if target is None and self.known_resource_spots:
            target = self.known_resource_spots[0]

        if target:
            self.position = self._step_toward(target, grid_world)
            return {"action": "move", "target": list(target)}
        return self._move_random(grid_world)

    def _move_random(self, grid_world) -> dict:
        for _ in range(4):
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            nx = self.position[0] + dx
            ny = self.position[1] + dy
            if grid_world.in_bounds(nx, ny):
                self.position = (nx, ny)
                return {"action": "move", "dx": dx, "dy": dy}
        return {"action": "idle"}

    def _explore(self, grid_world) -> dict:
        """Bias movement toward areas visited least recently."""
        recent = {m.get("pos") for m in self.short_term_memory[-8:]}
        for _ in range(6):
            dx = random.choice([-2, -1, 0, 1, 2])
            dy = random.choice([-2, -1, 0, 1, 2])
            nx = self.position[0] + dx
            ny = self.position[1] + dy
            if grid_world.in_bounds(nx, ny) and (nx, ny) not in recent:
                self.position = (nx, ny)
                return {"action": "explore", "dx": dx, "dy": dy}
        return self._move_random(grid_world)

    def _try_communicate(self, comm_system) -> dict:
        msg, mtype = self._build_message()
        if msg:
            comm_system.broadcast(self, msg, msg_type=mtype)
            return {"action": "communicate", "msg": msg, "msg_type": mtype}
        return {"action": "idle"}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _step_toward(self, target: tuple[int, int], grid_world) -> tuple[int, int]:
        x, y = self.position
        dx = 1 if target[0] > x else (-1 if target[0] < x else 0)
        dy = 1 if target[1] > y else (-1 if target[1] < y else 0)
        nx, ny = x + dx, y + dy
        if grid_world.in_bounds(nx, ny):
            return (nx, ny)
        return self.position

    def _scan_nearby_resources(self, grid_world, radius: int = 10) -> None:
        for tile in grid_world.resource_tiles:
            if tile.depleted:
                continue
            d = abs(tile.x - self.position[0]) + abs(tile.y - self.position[1])
            if d <= radius and (tile.x, tile.y) not in self.known_resource_spots:
                self.known_resource_spots.append((tile.x, tile.y))

    def _nearest_resource(self, grid_world, radius: int):
        best_dist = float("inf")
        best = None
        for tile in grid_world.resource_tiles:
            if tile.depleted:
                continue
            d = abs(tile.x - self.position[0]) + abs(tile.y - self.position[1])
            if d < radius and d < best_dist:
                best_dist = d
                best = (tile.x, tile.y)
        return best

    def _build_message(self) -> tuple[str | None, str]:
        candidates: list[tuple[str, str]] = []

        if self.known_resource_spots:
            x, y = random.choice(self.known_resource_spots)
            candidates.append((f"res {x} {y}", "resource_info"))

        if self.inventory:
            rtype = random.choice(list(self.inventory.keys()))
            candidates.append((f"have {rtype}", "inventory_share"))

        if self.energy < 20.0:
            candidates.append((f"need help", "distress"))

        if not candidates:
            if random.random() < 0.15:
                candidates.append((f"at {self.position[0]} {self.position[1]}", "position"))
            else:
                return (None, "")

        text, mtype = random.choice(candidates)
        self.vocabulary.update(text.split())
        return (text, mtype)

    def receive(self, msg: dict) -> None:
        sender = msg.get("sender", -1)
        content = msg.get("content", "")

        self.vocabulary.update(content.split())
        self.short_term_memory.append({"type": "msg", "from": sender, "content": content, "tick": self.tick_count})
        self.social_links[sender] = self.social_links.get(sender, 0) + 0.1
        self.message_history.append(msg)

        parts = content.split()
        if len(parts) >= 3 and parts[0] == "res":
            try:
                self.known_resource_spots.append((int(parts[1]), int(parts[2])))
            except ValueError:
                pass

    def _maybe_consolidate_memory(self) -> None:
        if len(self.short_term_memory) <= self.config.short_term_memory_size:
            return
        important = sorted(self.short_term_memory, key=lambda m: m.get("tick", 0), reverse=True)
        keep = important[: self.config.long_term_memory_size // 10]
        self.long_term_memory.extend(keep)
        self.short_term_memory.clear()

    def snapshot(self) -> AgentSnapshot:
        return AgentSnapshot(
            agent_id=self.id,
            x=self.position[0],
            y=self.position[1],
            energy=round(self.energy, 1),
            inventory_size=len(self.inventory),
            vocabulary_size=len(self.vocabulary),
            strategy=self.strategy,
            last_action=self.last_action,
        )

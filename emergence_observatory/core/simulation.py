from __future__ import annotations
import random
import math
import json
from pathlib import Path
from collections import defaultdict
from typing import Optional

from ..config import SimulationConfig
from ..cognition import CognitionService
from ..memory import MemoryStore
from ..replay import Recorder
from ..metrics import MetricsCollector
from .world import World
from .agent import Agent

_DIRECTIONS = {
    "n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0),
    "ne": (1, -1), "nw": (-1, -1), "se": (1, 1), "sw": (-1, 1),
}


class Simulation:
    """LLM-native multi-agent tick loop.

    Each tick a random subset of agents act via the LLM.  All state is
    persisted to JSON after every tick.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.tick = 0
        self.running = False

        self.rng = random.Random(config.world_seed)
        self.world = World(config.world_width, config.world_height, config.world_seed)
        self.cognition = CognitionService(config)
        self.memory = MemoryStore(config.memory_path)
        self.recorder = Recorder(config.replay_path)
        self.metrics = MetricsCollector()

        self.agents: dict[int, Agent] = {}
        self.conversation_log: list[dict] = []

        self._init_agents()
        self._save_all()

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------

    def _init_agents(self) -> None:
        for i in range(self.config.num_agents):
            x = self.rng.randint(0, self.config.world_width - 1)
            y = self.rng.randint(0, self.config.world_height - 1)
            agent = Agent.create(i, x, y, 0, self.rng)
            agent.world = self.world
            self.agents[i] = agent

    def add_agent(self) -> int | None:
        if len(self.agents) >= self.config.max_agents:
            return None
        nid = max(self.agents.keys()) + 1 if self.agents else 0
        x = self.rng.randint(0, self.config.world_width - 1)
        y = self.rng.randint(0, self.config.world_height - 1)
        agent = Agent.create(nid, x, y, self.tick, self.rng)
        agent.world = self.world
        self.agents[nid] = agent
        return nid

    # ------------------------------------------------------------------
    # Tick loop
    # ------------------------------------------------------------------

    def step(self) -> dict:
        self.tick += 1
        self.world.regenerate()

        active = [a for a in self.agents.values() if a.status == "active"]
        self.rng.shuffle(active)
        batch = active[:self.config.agents_per_tick]

        for agent in batch:
            self._process_agent(agent)

        self.metrics.collect(self)
        self.recorder.flush()
        self._save_all()

        return self._build_snapshot()

    def _process_agent(self, agent: Agent) -> None:
        agent.tick_last_active = self.tick
        decision = self.cognition.decide(agent)
        if decision is None:
            return

        action = decision.get("action", "ignore")
        params = {k: v for k, v in decision.items() if k not in ("action", "reasoning")}
        reasoning = decision.get("reasoning", "")

        result = self._execute_action(agent, action, params)
        agent.total_actions += 1
        agent.energy -= 0.5

        event = {
            "tick": self.tick,
            "agent_id": agent.agent_id,
            "action": action,
            "params": params,
            "reasoning": reasoning,
            "result": result,
            "position": (agent.x, agent.y),
        }
        self.recorder.record(event)
        self._save_agent(agent)

    def _execute_action(self, agent: Agent, action: str, params: dict) -> dict:
        result = {"success": True, "message": ""}

        if action == "move":
            dir_key = str(params.get("direction", "n")).lower()
            dx, dy = _DIRECTIONS.get(dir_key, (0, 0))
            nx, ny = agent.x + dx, agent.y + dy
            if self.world.in_bounds(nx, ny):
                agent.x, agent.y = nx, ny
                loc = self.world.get_location(nx, ny)
                result["message"] = f"Moved to {loc.name}."
                agent.add_memory(f"Arrived at {loc.name}: {loc.description}", tick=self.tick)
            else:
                result["success"] = False
                result["message"] = "Cannot move there."

        elif action == "gather":
            gathered = self.world.gather_resources(agent.x, agent.y)
            if gathered:
                for rt, qty in gathered.items():
                    agent.inventory[rt] = agent.inventory.get(rt, 0) + qty
                    agent.learn_word(rt)
                result["message"] = f"Gathered {gathered}."
                agent.add_memory(f"Gathered {gathered} at {self.world.get_location(agent.x, agent.y).name}", tick=self.tick)
            else:
                result["message"] = "Nothing to gather here."

        elif action == "speak":
            target_id = params.get("target_id") or params.get("target")
            content = str(params.get("content", ""))[:300]
            if target_id is not None and target_id in self.agents:
                target = self.agents[target_id]
                target.add_memory(f"Agent {agent.agent_id} said: {content}", mtype="conversation", tick=self.tick)

                for word in content.split():
                    agent.learn_word(word)
                    target.learn_word(word)

                agent.adjust_relationship(target_id, 0.3)
                target.adjust_relationship(agent.agent_id, 0.2)

                self.conversation_log.append({
                    "tick": self.tick,
                    "from": agent.agent_id,
                    "to": target_id,
                    "content": content,
                })
                agent.conversation_history.append(self.conversation_log[-1])
                result["message"] = f"Spoke to Agent {target_id}."

                agent.add_memory(f"I told Agent {target_id}: {content}", mtype="conversation", tick=self.tick)
            else:
                # Broadcast to all nearby
                content = str(params.get("content", ""))[:300]
                nearby = [a for a in self.agents.values() if a.agent_id != agent.agent_id
                          and self.world.distance(agent.x, agent.y, a.x, a.y) < 8]
                for t in nearby:
                    t.add_memory(f"Agent {agent.agent_id} broadcast: {content}", mtype="conversation", tick=self.tick)
                    t.adjust_relationship(agent.agent_id, 0.1)
                    for word in content.split():
                        agent.learn_word(word)
                        t.learn_word(word)
                result["message"] = f"Broadcast to {len(nearby)} nearby."

        elif action == "remember":
            content = str(params.get("content", ""))[:200]
            if content:
                agent.episodic_memory.append({"tick": self.tick, "type": "consolidated", "content": content})
                if len(agent.episodic_memory) > 100:
                    agent.episodic_memory = agent.episodic_memory[-100:]
                result["message"] = "Memory consolidated."

        elif action == "teach":
            target_id = params.get("target_id") or params.get("target")
            word = str(params.get("word", ""))
            if target_id in self.agents and word:
                target = self.agents[target_id]
                target.learn_word(word)
                if word in agent.invented_words:
                    target.invented_words[word] = agent.invented_words[word]
                agent.adjust_relationship(target_id, 0.5)
                target.adjust_relationship(agent.agent_id, 0.4)
                result["message"] = f"Taught '{word}' to Agent {target_id}."

        elif action == "follow":
            target_id = params.get("target_id") or params.get("target")
            if target_id in self.agents:
                target = self.agents[target_id]
                dx = 1 if target.x > agent.x else (-1 if target.x < agent.x else 0)
                dy = 1 if target.y > agent.y else (-1 if target.y < agent.y else 0)
                nx, ny = agent.x + dx, agent.y + dy
                if self.world.in_bounds(nx, ny):
                    agent.x, agent.y = nx, ny
                agent.adjust_relationship(target_id, 0.2)
                result["message"] = f"Following Agent {target_id}."

        elif action == "share_resource":
            target_id = params.get("target_id") or params.get("target")
            rtype = str(params.get("resource", ""))
            qty = float(params.get("quantity", 1))
            if target_id in self.agents and rtype in agent.inventory and agent.inventory[rtype] >= qty:
                target = self.agents[target_id]
                agent.inventory[rtype] -= qty
                if agent.inventory[rtype] <= 0:
                    del agent.inventory[rtype]
                target.inventory[rtype] = target.inventory.get(rtype, 0) + qty
                agent.adjust_relationship(target_id, 0.8)
                target.adjust_relationship(agent.agent_id, 0.7)
                result["message"] = f"Shared {qty} {rtype} with Agent {target_id}."

        elif action == "invent_word":
            word = str(params.get("word", "")).lower().strip()[:30]
            meaning = str(params.get("meaning", ""))[:100]
            if word and word not in agent.invented_words and word not in agent.vocabulary:
                agent.invented_words[word] = meaning
                agent.learn_word(word)
                result["message"] = f"Invented word '{word}' meaning '{meaning}'."
                agent.add_memory(f"I invented the word '{word}' for '{meaning}'", tick=self.tick)

        elif action == "cooperate":
            target_id = params.get("target_id") or params.get("target")
            proposal = str(params.get("proposal", "let's cooperate"))[:200]
            if target_id in self.agents:
                alliance_name = f"Alliance_{min(agent.agent_id, target_id)}_{max(agent.agent_id, target_id)}"
                agent.alliances[target_id] = alliance_name
                self.agents[target_id].alliances[agent.agent_id] = alliance_name
                agent.adjust_relationship(target_id, 1.0)
                self.agents[target_id].adjust_relationship(agent.agent_id, 1.0)
                result["message"] = f"Proposed alliance with Agent {target_id}: {proposal}"

        else:
            result = {"success": True, "message": "Rested."}

        return result

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_agent(self, agent: Agent) -> None:
        self.memory.save_agent(agent.agent_id, agent.to_dict())

    def _save_all(self) -> None:
        for agent in self.agents.values():
            self.memory.save_agent(agent.agent_id, agent.to_dict())
        self.memory.save_world(self.world.to_dict())

    def _load_all(self) -> None:
        data = self.memory.load_world()
        if data:
            self.world = World(data["width"], data["height"])
        for aid in self.memory.list_agents():
            d = self.memory.load_agent(aid)
            if d:
                agent = Agent(**{k: v for k, v in d.items() if k != "world"})
                agent.world = self.world
                self.agents[aid] = agent

    # ------------------------------------------------------------------
    # Snapshot for viz
    # ------------------------------------------------------------------

    def _build_snapshot(self) -> dict:
        agents_data = [a.snapshot() for a in self.agents.values()]
        recent_convos = self.conversation_log[-20:]

        return {
            "tick": self.tick,
            "num_agents": len(self.agents),
            "agents": agents_data,
            "metrics": self.metrics.current(),
            "conversations": recent_convos,
        }

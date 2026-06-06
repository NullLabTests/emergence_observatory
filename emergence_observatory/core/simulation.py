from __future__ import annotations
import random
import math
from typing import Optional
from collections import defaultdict

from .agent import Agent
from .grid_world import GridWorld
from ..config import SimulationConfig
from ..communication import CommunicationSystem
from ..cognition import CognitionService
from ..metrics import MetricsCollector
from ..logging import EventLogger


class Simulation:
    """Orchestrates the entire agent-based model.

    Responsibilities:
      - Create / destroy agents
      - Step the grid-world and each agent each tick
      - Route novel events through the CognitionService
      - Collect emergence metrics
      - Serve snapshot data for the live visualiser
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.tick = 0
        self.running = False

        self.world = GridWorld(config.grid_width, config.grid_height, config)
        self.agents: dict[int, Agent] = {}
        self.comm_system = CommunicationSystem(config)
        self.cognition = CognitionService(config)
        self.metrics = MetricsCollector()
        self.logger = EventLogger()

        self._init_agents()

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------

    def _init_agents(self) -> None:
        for i in range(self.config.num_agents):
            x = random.randrange(0, self.config.grid_width)
            y = random.randrange(0, self.config.grid_height)
            agent = Agent(i, x, y, self.config)
            self.agents[i] = agent

    def add_agent(self) -> int | None:
        if len(self.agents) >= self.config.max_agents:
            return None
        nid = max(self.agents.keys()) + 1 if self.agents else 0
        x = random.randrange(0, self.config.grid_width)
        y = random.randrange(0, self.config.grid_height)
        self.agents[nid] = Agent(nid, x, y, self.config)
        return nid

    def remove_agent(self, agent_id: int) -> None:
        self.agents.pop(agent_id, None)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def step(self) -> dict:
        """Advance one simulation tick.  Returns a summary event dict."""
        self.tick += 1
        tick_events: list[dict] = []

        self.world.tick_resources()
        deliveries = self.comm_system.deliver(self.agents, self.tick)

        for agent in list(self.agents.values()):
            if agent.energy <= 0:
                self.remove_agent(agent.id)
                continue

            action_log = agent.step(self.world, self.comm_system)
            action_log["agent_id"] = agent.id
            action_log["tick"] = self.tick
            tick_events.append(action_log)
            self.logger.log(action_log)

            # Deliver any pending messages to this agent
            if agent.id in deliveries:
                for msg in deliveries[agent.id]:
                    agent.receive(msg)
                    self.logger.log({"tick": self.tick, "event": "msg_delivered", "to": agent.id, "msg": msg})

        # --- Cognition service (LLM routing) ---
        if self.config.llm_enabled:
            self._route_novel_events()

        # --- Metrics ---
        self.metrics.collect(self)

        # --- Snapshot for visualiser ---
        snapshot = self._build_snapshot()
        self.logger.log({"tick": self.tick, "event": "snapshot"})
        return snapshot

    def _route_novel_events(self) -> None:
        for agent in self.agents.values():
            if agent.ticks_since_llm < self.config.llm_cooldown_ticks:
                continue
            novelty = self.cognition.novelty_detector.score(agent)
            if novelty >= self.config.novelty_threshold:
                payload = {
                    "agent_id": agent.id,
                    "position": list(agent.position),
                    "energy": agent.energy,
                    "inventory": dict(agent.inventory),
                    "strategy": agent.strategy,
                    "recent_messages": agent.message_history[-5:],
                    "vocab_size": len(agent.vocabulary),
                }
                result = self.cognition.process_event(agent.id, payload)
                if result and result.get("strategy"):
                    agent.strategy = result["strategy"]
                agent.ticks_since_llm = 0
                self.logger.log({"tick": self.tick, "event": "llm_invocation", "agent_id": agent.id, "result": result})

    # ------------------------------------------------------------------
    # Snapshot for visualisation / metrics
    # ------------------------------------------------------------------

    def _build_snapshot(self) -> dict:
        agents_data = [a.snapshot() for a in self.agents.values()]

        # Build adjacency for social graph
        adj: dict[int, list[int]] = defaultdict(list)
        for a in self.agents.values():
            for peer_id in a.social_links:
                adj[a.id].append(peer_id)

        return {
            "tick": self.tick,
            "num_agents": len(self.agents),
            "agents": agents_data,
            "resources": self.world.resource_map(),
            "metrics": self.metrics.current(),
            "social_graph_edge_count": sum(len(v) for v in adj.values()),
        }

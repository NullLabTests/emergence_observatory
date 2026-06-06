from __future__ import annotations
import random
from collections import defaultdict
from typing import Optional

from ..config import SimulationConfig
from ..cognition import CognitionService
from ..cognition.proposal_system import ProposalRegistry
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
    """LLM-native multi-agent simulation with society-building, voting, and research."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.tick = 0
        self.running = False

        self.rng = random.Random(config.world_seed)
        self.world = World(config.world_width, config.world_height, config.world_seed)
        self.world.proposals = ProposalRegistry(
            quorum_pct=config.quorum_pct,
            vote_ticks=config.vote_ticks_open,
        )
        self.cognition = CognitionService(config)
        self.memory = MemoryStore(config.memory_path)
        self.recorder = Recorder(config.replay_path)
        self.metrics = MetricsCollector()

        self.agents: dict[int, Agent] = {}
        self.conversation_log: list[dict] = []

        self._init_agents()
        self._save_all()

    def _init_agents(self) -> None:
        for i in range(self.config.num_agents):
            x = self.rng.randint(0, self.config.world_width - 1)
            y = self.rng.randint(0, self.config.world_height - 1)
            agent = Agent.create(i, x, y, 0, self.rng)
            agent.world = self.world
            self.agents[i] = agent

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

        self._voting_phase()
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

    # ------------------------------------------------------------------
    # Voting phase — tally proposals each tick
    # ------------------------------------------------------------------

    def _voting_phase(self) -> None:
        closed = self.world.proposals.tally(len(self.agents), self.tick)
        for prop in closed:
            self.world.norms = self.world.proposals.norms
            self.recorder.record({
                "tick": self.tick,
                "event": "proposal_closed",
                "proposal_id": prop.id,
                "title": prop.title,
                "status": prop.status,
                "votes_for": len(prop.votes_for),
                "votes_against": len(prop.votes_against),
            })

    # ------------------------------------------------------------------
    # Action executor
    # ------------------------------------------------------------------

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
                agent.add_memory(f"Arrived at {loc.name}", tick=self.tick)
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
                agent.add_memory(f"Gathered {gathered}", tick=self.tick)
            else:
                result["message"] = "Nothing to gather."

        elif action == "speak":
            target_id = params.get("target_id") or params.get("target")
            content = str(params.get("content", ""))[:300]
            if target_id is not None and target_id in self.agents:
                target = self.agents[target_id]
                target.add_memory(f"Agent {agent.agent_id} said: {content}", mtype="conversation", tick=self.tick)
                for w in content.split():
                    agent.learn_word(w); target.learn_word(w)
                agent.adjust_relationship(target_id, 0.3)
                target.adjust_relationship(agent.agent_id, 0.2)
                self.conversation_log.append({"tick": self.tick, "from": agent.agent_id, "to": target_id, "content": content})
                agent.conversation_history.append(self.conversation_log[-1])
                result["message"] = f"Spoke to Agent {target_id}."
            else:
                content = str(params.get("content", ""))[:300]
                nearby = [a for a in self.agents.values() if a.agent_id != agent.agent_id
                          and self.world.distance(agent.x, agent.y, a.x, a.y) < 8]
                for t in nearby:
                    t.add_memory(f"Agent {agent.agent_id} broadcast: {content}", mtype="conversation", tick=self.tick)
                    t.adjust_relationship(agent.agent_id, 0.1)
                    for w in content.split():
                        agent.learn_word(w); t.learn_word(w)
                result["message"] = f"Broadcast to {len(nearby)}."

        elif action == "remember":
            content = str(params.get("content", ""))[:200]
            if content:
                agent.episodic_memory.append({"tick": self.tick, "type": "consolidated", "content": content})
                if len(agent.episodic_memory) > 200:
                    agent.episodic_memory = agent.episodic_memory[-200:]
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
                result["message"] = f"Shared {qty} {rtype}."

        elif action == "invent_word":
            word = str(params.get("word", "")).lower().strip()[:30]
            meaning = str(params.get("meaning", ""))[:100]
            if word and word not in agent.invented_words and word not in agent.vocabulary:
                agent.invented_words[word] = meaning
                agent.learn_word(word)
                result["message"] = f"Invented '{word}': {meaning}"
                agent.add_memory(f"I invented '{word}' for '{meaning}'", tick=self.tick)

        elif action == "cooperate":
            target_id = params.get("target_id") or params.get("target")
            proposal = str(params.get("proposal", "let's cooperate"))[:200]
            if target_id in self.agents:
                aname = f"Alliance_{min(agent.agent_id, target_id)}_{max(agent.agent_id, target_id)}"
                agent.alliances[target_id] = aname
                self.agents[target_id].alliances[agent.agent_id] = aname
                agent.adjust_relationship(target_id, 1.0)
                self.agents[target_id].adjust_relationship(agent.agent_id, 1.0)
                result["message"] = f"Alliance with Agent {target_id}."

        # --- NEW: Society actions ---

        elif action == "propose":
            title = str(params.get("title", "Untitled proposal"))[:100]
            desc = str(params.get("description", ""))[:300]
            ptype = str(params.get("ptype", "norm"))[:20]
            if title:
                pid = self.world.proposals.submit(agent.agent_id, title, desc, ptype, self.tick)
                agent.proposals_made += 1
                agent.social_rank += 0.3
                result["message"] = f"Submitted proposal #{pid}: {title}"
                agent.add_memory(f"I proposed '{title}'", mtype="proposal", tick=self.tick)

        elif action == "vote":
            pid = int(params.get("proposal_id", 0))
            vote_val = params.get("vote", True)
            if isinstance(vote_val, str):
                vote_val = vote_val.lower() in ("true", "yes", "1", "yea")
            if pid and self.world.proposals.vote(pid, agent.agent_id, vote_val):
                agent.votes_cast += 1
                side = "for" if vote_val else "against"
                result["message"] = f"Voted {side} on proposal #{pid}."

        elif action == "research":
            query = str(params.get("query", "new ideas"))[:100]
            if query:
                findings = self.cognition.research(query)
                for f in findings:
                    agent.add_knowledge(query, f["snippet"], source="research", tick=self.tick)
                    agent.research_findings.append(f)
                result["message"] = f"Researched '{query}': {len(findings)} findings."
                agent.add_memory(f"Researched '{query}' and learned new things", mtype="research", tick=self.tick)

        elif action == "hivemind":
            topic = str(params.get("topic", "general"))[:50]
            content = str(params.get("content", ""))[:200]
            if topic and content:
                if topic not in self.world.knowledge_repo:
                    self.world.knowledge_repo[topic] = []
                self.world.knowledge_repo[topic].append({
                    "tick": self.tick, "agent_id": agent.agent_id, "content": content,
                })
                agent.social_rank += 0.2
                result["message"] = f"Shared knowledge on '{topic}'."
                agent.add_memory(f"Shared knowledge about {topic}", mtype="hivemind", tick=self.tick)

        elif action == "form_group":
            gname = str(params.get("group_name", f"Group_{agent.agent_id}"))[:50]
            purpose = str(params.get("purpose", "mutual benefit"))[:200]
            gid = self.world._next_group_id
            self.world._next_group_id += 1
            self.world.groups[gid] = {"name": gname, "purpose": purpose, "members": [agent.agent_id], "tick": self.tick}
            agent.group_id = gid
            agent.social_rank += 0.5
            result["message"] = f"Formed group '{gname}' (ID {gid})."

        elif action == "join_group":
            gid = int(params.get("group_id", 0))
            if gid in self.world.groups and agent.group_id is None:
                self.world.groups[gid]["members"].append(agent.agent_id)
                agent.group_id = gid
                agent.adjust_relationship(params.get("inviter_id", -1), 0.4)
                result["message"] = f"Joined group {gid}."

        else:
            result = {"success": True, "message": "Rested."}

        return result

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_agent(self, agent: Agent) -> None:
        self.memory.save_agent(agent.agent_id, agent.to_dict())

    def _save_all(self) -> None:
        for a in self.agents.values():
            self.memory.save_agent(a.agent_id, a.to_dict())
        wd = self.world.to_dict()
        wd["norms"] = self.world.norms
        wd["knowledge_repo"] = self.world.knowledge_repo
        wd["groups"] = self.world.groups
        self.memory.save_world(wd)

    # ------------------------------------------------------------------
    # Snapshot for viz
    # ------------------------------------------------------------------

    def _build_snapshot(self) -> dict:
        agents_data = [a.snapshot() for a in self.agents.values()]
        recent_convos = self.conversation_log[-20:]

        props = self.world.proposals
        open_props = [{"id": p.id, "title": p.title, "ptype": p.ptype,
                        "for": len(p.votes_for), "against": len(p.votes_against)}
                       for p in props.open_proposals()]

        return {
            "tick": self.tick,
            "num_agents": len(self.agents),
            "agents": agents_data,
            "metrics": self.metrics.current(),
            "conversations": recent_convos,
            "proposals": open_props,
            "norms": self.world.norms[-10:],
            "knowledge_topics": list(self.world.knowledge_repo.keys()),
            "groups": {str(k): v["name"] for k, v in self.world.groups.items()},
        }

from __future__ import annotations
from typing import Optional

from .mistral_bridge import MistralBridge
from .prompts import AGENT_SYSTEM_PROMPT, WORLD_INTRO_PROMPT


class CognitionService:
    """Shared LLM cognition service with rate limiting.

    All agent-to-LLM calls flow through this singleton.  It formats
    prompts, dispatches to Mistral, and returns structured decisions.
    """

    def __init__(self, config):
        self.config = config
        self.bridge = MistralBridge(
            api_key=config.mistral_api_key,
            model=config.mistral_model,
            rate_limit_rpm=config.llm_rate_limit_rpm,
            retry_max=config.llm_retry_max,
            timeout=config.llm_timeout,
        )

    def decide(self, agent) -> dict | None:
        """Ask the LLM what action the agent should take this tick."""
        prompt = self._build_prompt(agent)
        return self.bridge.reason(prompt)

    def birth(self, agent) -> str | None:
        """Generate an agent's biography on first creation."""
        data = self.bridge.reason(WORLD_INTRO_PROMPT)
        if data and isinstance(data, dict):
            return data.get("biography") or data.get("content") or str(data)
        return None

    def _build_prompt(self, agent) -> str:
        loc = agent.world.get_location(agent.x, agent.y)
        nearby = agent.world.nearby_agents(agent.x, agent.y, radius=5, exclude=agent.agent_id)
        nearby_str = ", ".join(
            f"Agent {a.agent_id} ({a.status})" for a in nearby
        ) or "none"

        rels = dict(list(agent.relationship_memory.items())[:8])
        rel_str = "; ".join(
            f"Agent {k}: affinity {v:.1f}" for k, v in rels.items()
        ) or "none"

        mems = list(agent.short_term_memory) + list(agent.episodic_memory[-3:])
        mem_str = "\n".join(
            f"[{m.get('tick', '?')}] {m.get('content', str(m))[:200]}"
            for m in mems[-6:]
        ) or "none"

        inv = list(agent.inventory.keys())
        inv_str = ", ".join(inv) if inv else "empty"

        goals = agent.goals or ["explore and survive"]
        goals_str = "; ".join(goals)

        vocab = sorted(agent.vocabulary)
        vocab_str = ", ".join(vocab[-30:]) if vocab else "none yet"

        iw = agent.invented_words
        iw_str = "; ".join(f"{w}: {m}" for w, m in iw.items()) if iw else "none"

        allens = agent.alliances
        all_str = "; ".join(f"Agent {k}: {v}" for k, v in allens.items()) if allens else "none"

        return AGENT_SYSTEM_PROMPT.format(
            agent_id=agent.agent_id,
            biography=agent.biography or "A newly awakened entity.",
            personality=agent.personality,
            goals=goals_str,
            location_name=loc.name,
            x=agent.x, y=agent.y,
            location_desc=loc.description,
            location_resources=", ".join(loc.resources) if loc.resources else "none",
            energy=agent.energy,
            inventory_str=inv_str,
            nearby_str=nearby_str,
            relationships_str=rel_str,
            alliances_str=all_str,
            vocab_str=vocab_str,
            invented_words_str=iw_str,
            memories_str=mem_str,
        )

    def stats(self) -> dict:
        return dict(self.bridge.stats)

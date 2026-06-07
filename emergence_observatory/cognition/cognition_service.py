from __future__ import annotations
from typing import Optional

from .mistral_bridge import MistralBridge
from .serper_bridge import LLMResearcher
from .prompts import AGENT_SYSTEM_PROMPT


class CognitionService:
    """Shared LLM cognition service with built-in research capability.

    Research uses the LLM's own pre-training knowledge — no external
    web search API key needed.  The model generates plausible,
    grounded findings on any topic from its training data.
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
        self.researcher = LLMResearcher(self.bridge)

    def decide(self, agent) -> dict | None:
        prompt = self._build_prompt(agent)
        return self.bridge.reason(prompt)

    def research(self, query: str) -> list[dict]:
        return self.researcher.search(query)

    def _build_prompt(self, agent) -> str:
        loc = agent.world.get_location(agent.x, agent.y)
        nearby = agent.world.nearby_agents(agent.x, agent.y, radius=6, exclude=agent.agent_id)
        nearby_str = ", ".join(
            f"Agent {a.agent_id} (rank {getattr(a, 'social_rank', 0):.1f})"
            for a in nearby
        ) or "none"

        rels = dict(list(agent.relationship_memory.items())[:8])
        rel_str = "; ".join(f"Agent {k}: affinity {v:.1f}" for k, v in rels.items()) or "none"

        mems = list(agent.short_term_memory) + list(agent.episodic_memory[-3:])
        mem_str = "\n".join(
            f"[{m.get('tick', '?')}] {m.get('content', str(m))[:180]}"
            for m in mems[-6:]
        ) or "none"

        inv = list(agent.inventory.keys())
        inv_str = ", ".join(inv) if inv else "empty"

        goals = agent.goals or ["explore and survive"]
        goals_str = "; ".join(goals)

        vocab = sorted(agent.vocabulary)
        vocab_str = ", ".join(vocab[-40:]) if vocab else "none yet"

        iw = agent.invented_words
        iw_str = "; ".join(f"{w}: {m}" for w, m in iw.items()) if iw else "none"

        allens = agent.alliances
        all_str = "; ".join(f"Agent {k}: {v}" for k, v in allens.items()) if allens else "none"

        # Society context
        group_str = f"Group {agent.group_id}" if agent.group_id else "none"
        proposals = getattr(agent.world, "proposals", None)
        props = proposals.open_proposals() if proposals else []
        prop_str = "; ".join(
            f"#{p.id} '{p.title}' ({p.ptype})" for p in props[:5]
        ) or "none"

        norms = getattr(agent.world, "norms", [])
        norms_str = "; ".join(n["title"] for n in norms[-5:]) if norms else "none"

        ktopics = list(getattr(agent.world, "knowledge_repo", {}).keys())
        k_str = ", ".join(ktopics[-8:]) if ktopics else "none"

        return AGENT_SYSTEM_PROMPT.format(
            agent_id=agent.agent_id,
            biography=agent.biography or "A newly awakened entity.",
            personality=agent.personality,
            social_rank=agent.social_rank,
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
            group_str=group_str,
            vocab_str=vocab_str,
            invented_words_str=iw_str,
            proposals_str=prop_str,
            norms_str=norms_str,
            knowledge_str=k_str,
            memories_str=mem_str,
        )

    def stats(self) -> dict:
        return dict(self.bridge.stats)

from __future__ import annotations
import random
from dataclasses import dataclass, field, asdict

_PERSONALITY_TRAITS = [
    "curious", "cautious", "brave", "generous", "suspicious",
    "playful", "thoughtful", "impulsive", "loyal", "independent",
    "inventive", "proud", "gentle", "competitive", "trusting",
    "diplomatic", "ambitious", "protective", "explorative",
]

_SOCIAL_GOALS = [
    "build a thriving community",
    "establish laws and governance",
    "create a shared belief system",
    "become a respected leader",
    "unite all agents under common purpose",
    "invent a writing system for the society",
    "establish trade routes between groups",
    "teach the young agents wisdom",
    "build monuments to collective achievement",
    "create a fair system for sharing resources",
]

_GOAL_TEMPLATES = _SOCIAL_GOALS + [
    "explore the {direction} part of the world",
    "find rare {resource}",
    "make friends with other agents",
    "discover the meaning of this world",
    "collect as many different resources as possible",
    "learn everything there is to know",
    "become the wisest agent",
    "invent a shared language",
]

_BIOS = [
    "emerged near a {loc} and felt an immediate pull toward {goal}",
    "awoke with a vivid memory of {memory} and a drive to {goal}",
    "first became aware while watching light dance through {loc}",
    "materialized with a strange sense of purpose: {goal}",
    "opened their eyes to the world and decided to {goal}",
]


@dataclass
class Agent:
    agent_id: int
    personality: str
    biography: str
    x: int
    y: int
    energy: float = 100.0
    status: str = "active"
    inventory: dict[str, float] = field(default_factory=dict)
    short_term_memory: list[dict] = field(default_factory=list)
    episodic_memory: list[dict] = field(default_factory=list)
    relationship_memory: dict[int, float] = field(default_factory=dict)
    vocabulary: set[str] = field(default_factory=set)
    invented_words: dict[str, str] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    alliances: dict[int, str] = field(default_factory=dict)
    tick_created: int = 0
    tick_last_active: int = 0
    total_actions: int = 0
    conversation_history: list[dict] = field(default_factory=list)

    # Society layer
    knowledge_base: list[dict] = field(default_factory=list)
    votes_cast: int = 0
    proposals_made: int = 0
    social_rank: float = 0.0
    group_id: Optional[int] = None
    research_findings: list[dict] = field(default_factory=list)

    world: object = None

    def snapshot(self) -> dict:
        nearby = []
        if self.world:
            nearby = self.world.nearby_agents(self.x, self.y, radius=6, exclude=self.agent_id)
        return {
            "agent_id": self.agent_id,
            "x": self.x, "y": self.y,
            "energy": round(self.energy, 1),
            "status": self.status,
            "personality": self.personality,
            "goals": list(self.goals),
            "inventory": dict(self.inventory),
            "vocab_size": len(self.vocabulary),
            "invented_words": dict(self.invented_words),
            "num_alliances": len(self.alliances),
            "relationships": len(self.relationship_memory),
            "total_actions": self.total_actions,
            "social_rank": round(self.social_rank, 2),
            "group_id": self.group_id,
            "votes_cast": self.votes_cast,
            "proposals_made": self.proposals_made,
            "nearby_agents": [a.agent_id for a in nearby],
        }

    def to_dict(self) -> dict:
        d = asdict(self)
        d["vocabulary"] = list(self.vocabulary)
        d.pop("world", None)
        return d

    @classmethod
    def create(cls, agent_id: int, x: int, y: int, tick: int, rng: random.Random) -> Agent:
        n_traits = rng.randint(2, 4)
        traits = rng.sample(_PERSONALITY_TRAITS, min(n_traits, len(_PERSONALITY_TRAITS)))
        personality = ", ".join(traits)

        n_goals = rng.randint(1, 2)
        dirs = ["northern", "southern", "eastern", "western", "central"]
        resources = ["crystals", "food", "water", "herbs", "stone"]
        locs = ["a crystal cave", "a river bank", "an ancient tree", "a rocky outcrop", "a flower field"]
        mems = ["a golden light", "a voice speaking unknown words", "the feeling of floating", "a vast empty plain"]

        goals = []
        for _ in range(n_goals):
            g = rng.choice(_GOAL_TEMPLATES)
            if "{" in g:
                goals.append(g.format(direction=rng.choice(dirs), resource=rng.choice(resources)))
            else:
                goals.append(g)

        bio = rng.choice(_BIOS).format(
            loc=rng.choice(locs),
            goal=goals[0],
            memory=rng.choice(mems),
        )
        return cls(agent_id=agent_id, personality=personality, biography=bio,
                   x=x, y=y, goals=goals, tick_created=tick)

    def add_memory(self, content: str, mtype: str = "experience", tick: int = 0) -> None:
        mem = {"tick": tick, "type": mtype, "content": content}
        self.short_term_memory.append(mem)
        self.episodic_memory.append(mem)
        if len(self.short_term_memory) > 30:
            self.short_term_memory = self.short_term_memory[-30:]
        if len(self.episodic_memory) > 200:
            self.episodic_memory = self.episodic_memory[-200:]

    def learn_word(self, word: str) -> None:
        if word:
            self.vocabulary.add(word.lower().strip(".,!?;:"))

    def adjust_relationship(self, other_id: int, delta: float) -> None:
        current = self.relationship_memory.get(other_id, 0.0)
        self.relationship_memory[other_id] = max(-5.0, min(5.0, current + delta))
        self.social_rank = max(-5.0, min(5.0, self.social_rank + delta * 0.05))

    def add_knowledge(self, topic: str, content: str, source: str = "research", tick: int = 0) -> None:
        self.knowledge_base.append({
            "tick": tick, "topic": topic, "content": content, "source": source,
        })
        if len(self.knowledge_base) > 50:
            self.knowledge_base = self.knowledge_base[-50:]
        for word in content.split()[:10]:
            self.learn_word(word)

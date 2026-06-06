from __future__ import annotations
import random
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

_PERSONALITY_TRAITS = [
    "curious", "cautious", "brave", "generous", "suspicious",
    "playful", "thoughtful", "impulsive", "loyal", "independent",
    "inventive", "proud", "gentle", "competitive", "trusting",
]

_GOAL_TEMPLATES = [
    "explore the {direction} part of the world",
    "find rare {resource}",
    "make friends with other agents",
    "discover the meaning of this world",
    "collect as many different resources as possible",
    "build a safe shelter",
    "learn everything there is to know",
    "become the wisest agent",
    "protect the {resource} in the {direction}",
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

    # Back-reference set by simulation
    world: object = None

    def snapshot(self) -> dict:
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
            goals.append(g.format(direction=rng.choice(dirs), resource=rng.choice(resources)))

        bio = rng.choice(_BIOS).format(
            loc=rng.choice(locs),
            goal=goals[0],
            memory=rng.choice(mems),
        )

        return cls(
            agent_id=agent_id,
            personality=personality,
            biography=bio,
            x=x, y=y,
            goals=goals,
            tick_created=tick,
        )


    def add_memory(self, content: str, mtype: str = "experience", tick: int = 0) -> None:
        mem = {"tick": tick, "type": mtype, "content": content}
        self.short_term_memory.append(mem)
        self.episodic_memory.append(mem)
        if len(self.short_term_memory) > 20:
            self.short_term_memory = self.short_term_memory[-20:]

    def learn_word(self, word: str) -> None:
        if word:
            self.vocabulary.add(word.lower().strip(".,!?;:"))

    def adjust_relationship(self, other_id: int, delta: float) -> None:
        current = self.relationship_memory.get(other_id, 0.0)
        self.relationship_memory[other_id] = max(-5.0, min(5.0, current + delta))

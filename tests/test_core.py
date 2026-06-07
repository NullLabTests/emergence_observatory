from __future__ import annotations
import sys, random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emergence_observatory.config import SimulationConfig
from emergence_observatory.core.world import World
from emergence_observatory.core.agent import Agent


class TestWorld:
    def test_in_bounds(self):
        w = World(50, 40, seed=1)
        assert w.in_bounds(0, 0)
        assert w.in_bounds(49, 39)
        assert not w.in_bounds(-1, 0)
        assert not w.in_bounds(0, -1)
        assert not w.in_bounds(50, 0)
        assert not w.in_bounds(0, 40)

    def test_regenerate(self):
        w = World(10, 10, seed=1)
        assert len(w.locations) == 100  # all tiles have a location

    def test_distance(self):
        w = World(50, 40, seed=1)
        assert w.distance(0, 0, 3, 4) == 5.0

    def test_nearby_agents(self):
        w = World(50, 40, seed=1)
        rng = random.Random(42)
        from emergence_observatory.core.agent import Agent
        a1 = Agent.create(0, 10, 10, 0, rng)
        a2 = Agent.create(1, 12, 10, 0, rng)  # within radius 6
        a3 = Agent.create(2, 30, 30, 0, rng)  # outside radius 6
        w._agent_cache = {0: a1, 1: a2, 2: a3}
        nearby = w.nearby_agents(10, 10, radius=6, exclude=0)
        assert len(nearby) == 1
        assert nearby[0].agent_id == 1


class TestAgent:
    def test_create(self):
        rng = random.Random(42)
        a = Agent.create(0, 10, 20, 0, rng)
        assert a.agent_id == 0
        assert a.x == 10
        assert a.y == 20
        assert a.personality != ""
        assert a.biography != ""
        assert len(a.goals) > 0
        assert a.status == "active"

    def test_learn_word(self):
        rng = random.Random(42)
        a = Agent.create(0, 0, 0, 0, rng)
        a.learn_word("hello")
        assert "hello" in a.vocabulary
        a.learn_word("hello")
        assert len(a.vocabulary) == 1

    def test_invent_word(self):
        rng = random.Random(42)
        a = Agent.create(0, 0, 0, 0, rng)
        a.invented_words["lumi"] = "the dancing light"
        assert "lumi" in a.invented_words
        assert a.invented_words["lumi"] == "the dancing light"

    def test_adjust_relationship(self):
        rng = random.Random(42)
        a = Agent.create(0, 0, 0, 0, rng)
        a.adjust_relationship(5, 1.0)
        assert a.relationship_memory.get(5, 0) == 1.0
        a.adjust_relationship(5, -0.5)
        assert a.relationship_memory.get(5, 0) == 0.5

    def test_add_memory(self):
        rng = random.Random(42)
        a = Agent.create(0, 0, 0, 0, rng)
        a.add_memory("test memory", tick=1)
        assert len(a.short_term_memory) > 0
        assert a.short_term_memory[-1]["content"] == "test memory"

    def test_add_knowledge(self):
        rng = random.Random(42)
        a = Agent.create(0, 0, 0, 0, rng)
        a.add_knowledge("light", "Light is electromagnetic radiation", source="research", tick=1)
        assert len(a.knowledge_base) == 1
        assert a.knowledge_base[0]["topic"] == "light"
        assert a.knowledge_base[0]["content"] == "Light is electromagnetic radiation"

    def test_snapshot(self):
        rng = random.Random(42)
        a = Agent.create(7, 5, 10, 0, rng)
        s = a.snapshot()
        assert s["agent_id"] == 7
        assert s["x"] == 5
        assert s["y"] == 10
        assert s["energy"] > 0
        assert "personality" in s
        assert "goals" in s
        assert "invented_words" in s
        assert "social_rank" in s


class TestConfig:
    def test_defaults(self):
        c = SimulationConfig()
        assert c.num_agents == 100
        assert c.world_width == 80
        assert c.world_height == 60
        assert c.llm_rate_limit_rpm == 120
        assert c.vote_ticks_open == 8

    def test_custom(self):
        c = SimulationConfig(num_agents=15, world_width=50, world_height=40, max_ticks=20)
        assert c.num_agents == 15
        assert c.max_ticks == 20

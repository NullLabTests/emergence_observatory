from __future__ import annotations
import random
import math
from dataclasses import dataclass, field
from typing import Optional

_LOCATION_NAMES = [
    "Sunrise Clearing", "River Bend", "Ancient Oak Grove", "Crystal Cove",
    "Whispering Cave", "High Meadow", "Stone Circle", "Fern Grotto",
    "Lily Pond", "Iron Ridge", "Silver Stream", "Thorn Thicket",
    "Sky View Plateau", "Deepwood Thicket", "Obsidian Field",
    "Moonlight Marsh", "Amber Hill", "Cobalt Basin", "Scarlet Dunes",
    "Frost Hollow", "Emerald Pool", "Copper Gulch", "Twilight Glen",
    "Basalt Spire", "Coral Flats",
]

_RESOURCE_DESCRIPTIONS: dict[str, list[str]] = {
    "food": ["sweet berries", "wild mushrooms", "edible roots", "nutritious nuts"],
    "water": ["fresh spring water", "clear stream water", "dew drops"],
    "crystal": ["glowing blue crystals", "sharp red crystals", "translucent green gems", "pulsing purple stones"],
    "stone": ["smooth river stones", "sharp flint", "heavy granite"],
    "wood": ["dry branches", "sturdy logs", "flexible twigs"],
    "herb": ["aromatic herbs", "medicinal leaves", "fragrant flowers"],
}

_RESOURCE_COLORS: dict[str, str] = {
    "food": "#3fb950",
    "water": "#58a6ff",
    "crystal": "#bc8cff",
    "stone": "#8b949e",
    "wood": "#d29922",
    "herb": "#7ee787",
}


@dataclass
class Location:
    x: int
    y: int
    name: str
    description: str
    resources: list[str] = field(default_factory=list)
    resource_counts: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "x": self.x, "y": self.y,
            "name": self.name,
            "description": self.description,
            "resources": self.resources,
            "resource_counts": self.resource_counts,
        }


class World:
    """A 2D world of named locations with resources.

    Agents occupy locations and can gather resources, move between
    adjacent locations, and encounter one another.
    """

    def __init__(self, width: int, height: int, seed: int = 42):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.locations: dict[tuple[int, int], Location] = {}
        self._generate()

    def _generate(self) -> None:
        name_pool = list(_LOCATION_NAMES)
        self.rng.shuffle(name_pool)
        resource_types = list(_RESOURCE_DESCRIPTIONS.keys())

        # Place named locations at interesting points
        num_locations = min(len(name_pool), (self.width * self.height) // 40)
        for i in range(num_locations):
            x = self.rng.randint(1, self.width - 2)
            y = self.rng.randint(1, self.height - 2)
            name = name_pool[i] if i < len(name_pool) else f"Zone {i}"
            n_resources = self.rng.randint(1, 3)
            chosen = self.rng.sample(resource_types, min(n_resources, len(resource_types)))
            desc_parts = []
            counts = {}
            for rt in chosen:
                items = _RESOURCE_DESCRIPTIONS[rt]
                desc_parts.append(self.rng.choice(items))
                counts[rt] = round(self.rng.uniform(5, 30), 1)

            desc = f"A place with {' and '.join(desc_parts)}."
            self.locations[(x, y)] = Location(
                x=x, y=y, name=name, description=desc,
                resources=chosen, resource_counts=counts,
            )

        # Fill empty cells with generic locations
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in self.locations:
                    generic = self.rng.choice(["open field", "dense brush", "rocky ground", "sandy patch", "grassy knoll"])
                    self.locations[(x, y)] = Location(
                        x=x, y=y,
                        name=f"{generic}",
                        description=f"An unremarkable patch of {generic}.",
                        resources=[],
                        resource_counts={},
                    )

    def get_location(self, x: int, y: int) -> Location:
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        return self.locations.get((x, y), Location(x, y, "Void", "Empty."))

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        result = []
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                result.append((nx, ny))
        return result

    def nearby_agents(self, x: int, y: int, radius: int = 5, exclude: int = -1) -> list:
        from .agent import Agent
        # This is populated by the simulation
        return []

    def distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        return math.hypot(x2 - x1, y2 - y1)

    def gather_resources(self, x: int, y: int, agent_skill: float = 1.0) -> dict[str, float]:
        loc = self.get_location(x, y)
        gathered: dict[str, float] = {}
        for rt in list(loc.resource_counts.keys()):
            if loc.resource_counts[rt] > 0:
                amount = min(loc.resource_counts[rt], round(3 + self.rng.random() * 5, 1))
                loc.resource_counts[rt] -= amount
                gathered[rt] = round(amount * agent_skill, 1)
        return gathered

    def regenerate(self, rate: float = 0.02) -> None:
        for loc in self.locations.values():
            for rt in loc.resources:
                if rt in loc.resource_counts:
                    max_val = 20.0
                    if loc.resource_counts[rt] < max_val:
                        inc = max_val * rate * self.rng.random()
                        loc.resource_counts[rt] = min(max_val, loc.resource_counts[rt] + round(inc, 1))

    def to_dict(self) -> dict:
        locs = {f"{x},{y}": loc.to_dict() for (x, y), loc in self.locations.items()}
        return {"width": self.width, "height": self.height, "locations": locs}

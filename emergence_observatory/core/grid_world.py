from __future__ import annotations
import random
import math
from typing import Optional

from .resource import ResourceTile


class GridWorld:
    """A 2D toroidal or bounded grid that holds resources and validates agent positions."""

    def __init__(self, width: int, height: int, config):
        self.width = width
        self.height = height
        self.config = config
        self.resource_tiles: list[ResourceTile] = []

        self._populate_resources()

    # ------------------------------------------------------------------
    # Resource management
    # ------------------------------------------------------------------

    def _populate_resources(self) -> None:
        count = int(self.width * self.height * self.config.resource_density)
        rtypes = self.config.resource_types
        for _ in range(count):
            x = random.randrange(0, self.width)
            y = random.randrange(0, self.height)
            rt = random.choice(rtypes)
            amount = random.uniform(5.0, 20.0)
            self.resource_tiles.append(ResourceTile(x, y, rt, amount, max_amount=amount))

    def resources_at(self, pos: tuple[int, int]) -> list[ResourceTile]:
        return [t for t in self.resource_tiles if (t.x, t.y) == pos and not t.depleted]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tick_resources(self) -> None:
        for t in self.resource_tiles:
            t.regenerate(self.config.resource_regeneration_rate)

    def scan_resources(self, pos: tuple[int, int], radius: float) -> list[tuple[int, int]]:
        spots = []
        for t in self.resource_tiles:
            if t.depleted:
                continue
            d = math.hypot(t.x - pos[0], t.y - pos[1])
            if d <= radius:
                spots.append((t.x, t.y))
        return spots

    # ------------------------------------------------------------------
    # Serialisation helpers for visualisation / metrics
    # ------------------------------------------------------------------

    def resource_map(self) -> list[dict]:
        return [t.to_dict() for t in self.resource_tiles if not t.depleted]

from __future__ import annotations
from typing import Optional


class ResourceTile:
    """A tile on the grid that may contain one or more resource types."""

    def __init__(self, x: int, y: int, resource_type: str, amount: float = 10.0, max_amount: float = 10.0):
        self.x = x
        self.y = y
        self.resource_type = resource_type
        self.amount = amount
        self.max_amount = max_amount

    @property
    def depleted(self) -> bool:
        return self.amount <= 0

    def gather(self, quantity: float = 5.0) -> float:
        taken = min(quantity, self.amount)
        self.amount -= taken
        return taken

    def regenerate(self, rate: float = 0.01) -> None:
        if self.amount < self.max_amount:
            self.amount = min(self.max_amount, self.amount + self.max_amount * rate)

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "type": self.resource_type,
            "amount": round(self.amount, 1),
        }

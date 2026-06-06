from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Message:
    sender_id: int
    content: str
    tick: int = -1
    msg_type: str = "broadcast"

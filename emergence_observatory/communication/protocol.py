from __future__ import annotations
import math
from collections import defaultdict


class CommunicationSystem:
    """Manages agent-to-agent message passing within communication range."""

    def __init__(self, config):
        self.config = config
        self._inbox: dict[int, list[dict]] = defaultdict(list)
        self._outbox: list[dict] = []
        self.total_messages: int = 0

    def broadcast(self, sender, text: str, msg_type: str = "broadcast") -> None:
        self._outbox.append({
            "sender": sender.id,
            "sender_pos": sender.position,
            "content": text[: self.config.max_message_length],
            "msg_type": msg_type,
        })
        self.total_messages += 1

    def direct(self, sender, recipient_id: int, text: str, msg_type: str = "direct") -> None:
        self._outbox.append({
            "sender": sender.id,
            "sender_pos": sender.position,
            "recipient": recipient_id,
            "content": text[: self.config.max_message_length],
            "msg_type": msg_type,
        })
        self.total_messages += 1

    def deliver(self, agents: dict[int, object], tick: int) -> dict[int, list[dict]]:
        """Route all pending outbox messages to in-range recipients."""
        deliveries: dict[int, list[dict]] = defaultdict(list)

        for msg in self._outbox:
            sx, sy = msg["sender_pos"]
            for aid, agent in agents.items():
                if aid == msg["sender"]:
                    continue
                dist = abs(agent.position[0] - sx) + abs(agent.position[1] - sy)
                if dist <= self.config.communication_range:
                    deliveries[aid].append({**msg, "tick": tick})

        self._outbox.clear()
        return deliveries

    def stats(self) -> dict:
        return {"total_messages": self.total_messages}

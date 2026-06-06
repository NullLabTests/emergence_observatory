from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Proposal:
    id: int
    proposer_id: int
    title: str
    description: str
    ptype: str = "norm"  # norm, rule, action, goal
    votes_for: set[int] = field(default_factory=set)
    votes_against: set[int] = field(default_factory=set)
    status: str = "open"  # open, passed, rejected
    tick_created: int = 0
    tick_closed: int = 0
    outcome: str = ""


class ProposalRegistry:
    """Manages proposals, voting, and collective norms."""

    def __init__(self, quorum_pct: float = 0.3, vote_ticks: int = 10):
        self.proposals: dict[int, Proposal] = {}
        self.norms: list[dict] = []
        self._next_id = 1
        self.quorum_pct = quorum_pct
        self.vote_ticks = vote_ticks

    def submit(self, proposer_id: int, title: str, description: str,
               ptype: str = "norm", tick: int = 0) -> int:
        pid = self._next_id
        self._next_id += 1
        self.proposals[pid] = Proposal(
            id=pid, proposer_id=proposer_id,
            title=title[:100], description=description[:300],
            ptype=ptype, tick_created=tick,
        )
        return pid

    def vote(self, proposal_id: int, agent_id: int, vote: bool) -> bool:
        prop = self.proposals.get(proposal_id)
        if not prop or prop.status != "open":
            return False
        if vote:
            prop.votes_for.add(agent_id)
        else:
            prop.votes_against.add(agent_id)
        return True

    def tally(self, total_agents: int, tick: int) -> list[Proposal]:
        closed = []
        for prop in list(self.proposals.values()):
            if prop.status != "open":
                continue
            age = tick - prop.tick_created
            if age < self.vote_ticks:
                continue
            total_votes = len(prop.votes_for) + len(prop.votes_against)
            quorum = int(total_agents * self.quorum_pct)
            if total_votes >= quorum:
                passed = len(prop.votes_for) > len(prop.votes_against)
                prop.status = "passed" if passed else "rejected"
                prop.tick_closed = tick
                if passed:
                    self.norms.append({
                        "proposal_id": prop.id,
                        "title": prop.title,
                        "description": prop.description,
                        "type": prop.ptype,
                        "tick_passed": tick,
                        "proposer_id": prop.proposer_id,
                    })
                closed.append(prop)
        return closed

    def open_proposals(self) -> list[Proposal]:
        return [p for p in self.proposals.values() if p.status == "open"]

    def to_dict(self) -> dict:
        return {
            "norms": self.norms,
            "open_count": len(self.open_proposals()),
            "total_passed": sum(1 for p in self.proposals.values() if p.status == "passed"),
        }

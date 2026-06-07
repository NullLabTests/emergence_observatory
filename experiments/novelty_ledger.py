from __future__ import annotations
from collections import defaultdict


class NoveltyLedger:
    """Tracks every invented word through its full lifecycle.

    For each word we record:
      - birth tick and inventor
      - peak adoption (max agents using it simultaneously)
      - last tick it was seen
      - whether it is considered extinct
      - governance mode active during its lifetime
    """

    def __init__(self, extinction_delay: int = 20):
        self.extinction_delay = extinction_delay
        self._words: dict[str, dict] = {}
        self._history: list[dict] = []

    def observe(self, tick: int, agents: list, governance: str = "none") -> None:
        """Call every tick with the current agent list to update the ledger."""
        current_words: dict[str, int] = defaultdict(int)
        for a in agents:
            for w in a.invented_words:
                current_words[w] += 1

        for word, count in current_words.items():
            if word not in self._words:
                self._words[word] = {
                    "word": word,
                    "birth_tick": tick,
                    "birth_agent": next((a.agent_id for a in agents if word in a.invented_words), -1),
                    "peak_adoption": count,
                    "peak_tick": tick,
                    "last_seen": tick,
                    "current_adoption": count,
                    "extinct": False,
                    "extinction_tick": None,
                    "governance": governance,
                }
            else:
                entry = self._words[word]
                entry["last_seen"] = tick
                entry["current_adoption"] = count
                if count > entry["peak_adoption"]:
                    entry["peak_adoption"] = count
                    entry["peak_tick"] = tick

        # Mark extinct words
        for word, entry in self._words.items():
            if not entry["extinct"] and (tick - entry["last_seen"]) > self.extinction_delay:
                entry["extinct"] = True
                entry["extinction_tick"] = tick

    def snapshot(self) -> list[dict]:
        return sorted(self._words.values(), key=lambda x: x["birth_tick"])

    def summary(self) -> dict:
        if not self._words:
            return {}
        alive = [w for w in self._words.values() if not w["extinct"]]
        extinct = [w for w in self._words.values() if w["extinct"]]
        lifespans = []
        for w in self._words.values():
            end = w.get("extinction_tick") or w.get("last_seen", 9999)
            lifespans.append(end - w["birth_tick"])
        return {
            "total_words_invented": len(self._words),
            "alive_words": len(alive),
            "extinct_words": len(extinct),
            "mean_lifetime_ticks": round(sum(lifespans) / len(lifespans), 1) if lifespans else 0.0,
            "median_lifetime_ticks": sorted(lifespans)[len(lifespans) // 2] if lifespans else 0,
            "max_lifetime_ticks": max(lifespans) if lifespans else 0,
            "max_peak_adoption": max((w["peak_adoption"] for w in self._words.values()), default=0),
            "words": self.snapshot(),
        }

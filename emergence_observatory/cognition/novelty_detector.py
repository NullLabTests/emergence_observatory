from __future__ import annotations
import math


class NoveltyDetector:
    """Heuristic novelty scoring for agent state.

    A score in [0, 1] determines whether the agent's current situation is
    novel enough to warrant an expensive LLM call.  The score combines:

      - *Vocabulary novelty*: how many new words appeared recently.
      - *Interaction novelty*: how many unique agents interacted with.
      - *Starvation/danger signals*: critically low energy or inventory.
    """

    def __init__(self):
        self._history: dict[int, list[float]] = {}

    def score(self, agent) -> float:
        vocab_novelty = self._vocab_novelty(agent)
        social_novelty = self._social_novelty(agent)
        stress = self._stress_signal(agent)
        raw = 0.3 * vocab_novelty + 0.3 * social_novelty + 0.4 * stress
        return min(1.0, raw)

    def _vocab_novelty(self, agent) -> float:
        if len(agent.vocabulary) < 2:
            return 0.0
        recent_words = set()
        for m in agent.short_term_memory[-5:]:
            if isinstance(m, dict) and "content" in m:
                recent_words.update(m["content"].split())
        overlap = recent_words & agent.vocabulary if agent.vocabulary else set()
        if not recent_words:
            return 0.0
        return 1.0 - (len(overlap) / len(recent_words))

    def _social_novelty(self, agent) -> float:
        unique = len(agent.social_links)
        # Saturate at 20 unique contacts
        return min(1.0, unique / 20.0)

    def _stress_signal(self, agent) -> float:
        stress = 0.0
        if agent.energy < 20.0:
            stress += 0.5
        if not agent.inventory:
            stress += 0.2
        return min(1.0, stress)

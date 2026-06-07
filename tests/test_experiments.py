from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.novelty_ledger import NoveltyLedger


class TestNoveltyLedger:
    def test_empty(self):
        ledger = NoveltyLedger(extinction_delay=5)
        s = ledger.summary()
        assert s == {}

    def test_word_birth(self):
        ledger = NoveltyLedger(extinction_delay=5)

        class FakeAgent:
            agent_id = 0
            invented_words = {"lumi": "light"}
            vocabulary = {"lumi"}

        agents = [FakeAgent()]
        ledger.observe(0, agents)
        s = ledger.summary()
        assert s["total_words_invented"] == 1
        assert s["alive_words"] == 1

    def test_word_birth_multiple_agents(self):
        ledger = NoveltyLedger(extinction_delay=5)

        class FakeAgent:
            def __init__(self, aid, words):
                self.agent_id = aid
                self.invented_words = words
                self.vocabulary = set(words.keys())

        agents = [FakeAgent(0, {"lumi": "light"}), FakeAgent(1, {"veth": "seek"})]
        ledger.observe(0, agents)
        s = ledger.summary()
        assert s["total_words_invented"] == 2
        assert s["alive_words"] == 2

    def test_word_extinction(self):
        ledger = NoveltyLedger(extinction_delay=2)

        class FakeAgent:
            def __init__(self, aid, words):
                self.agent_id = aid
                self.invented_words = words
                self.vocabulary = set(words.keys())

        ledger.observe(0, [FakeAgent(0, {"lumi": "light"})])
        ledger.observe(1, [FakeAgent(1, {})])
        ledger.observe(2, [FakeAgent(2, {})])
        # tick 3 = tick 0 + 3 > 2 delay → extinct
        ledger.observe(3, [FakeAgent(3, {})])
        s = ledger.summary()
        assert s["extinct_words"] == 1
        assert s["alive_words"] == 0

    def test_peak_adoption(self):
        ledger = NoveltyLedger(extinction_delay=5)

        class FakeAgent:
            def __init__(self, aid, words):
                self.agent_id = aid
                self.invented_words = words
                self.vocabulary = set(words.keys())

        ledger.observe(0, [FakeAgent(0, {"lumi": "light"}), FakeAgent(1, {"lumi": "light"})])
        ledger.observe(1, [FakeAgent(2, {"lumi": "light"})])
        s = ledger.summary()
        assert s["max_peak_adoption"] == 2

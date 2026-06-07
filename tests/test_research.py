"""Tests for LLM-based research. Skips if MISTRAL_API_KEY is not set."""

from __future__ import annotations
import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from emergence_observatory.cognition.mistral_bridge import MistralBridge
from emergence_observatory.cognition.serper_bridge import LLMResearcher


@pytest.mark.skipif(not os.environ.get("MISTRAL_API_KEY"), reason="MISTRAL_API_KEY not set")
class TestLLMResearcher:
    def test_research_returns_findings(self):
        bridge = MistralBridge(rate_limit_rpm=60, retry_max=1, timeout=15)
        researcher = LLMResearcher(bridge)
        results = researcher.search("community building and governance")
        assert len(results) >= 1
        for r in results:
            assert "title" in r
            assert "snippet" in r
            assert len(r["snippet"]) > 10

    def test_research_topic_specificity(self):
        bridge = MistralBridge(rate_limit_rpm=60, retry_max=1, timeout=15)
        researcher = LLMResearcher(bridge)
        results = researcher.search("how to build shelter from stone")
        assert len(results) >= 1
        assert any("stone" in r["snippet"].lower() or "shelter" in r["snippet"].lower() for r in results)

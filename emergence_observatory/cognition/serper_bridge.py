from __future__ import annotations
import os
import json
from typing import Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class SerperBridge:
    """Web search via Serper.dev Google Search API.

    Agents use this to research new ideas, discover concepts, and
    bring external knowledge into the simulation.  Falls back to a
    synthetic result when the API key is absent.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SERPER_API_KEY", "")
        self._fallback = not self.api_key or not HAS_HTTPX

    def search(self, query: str, num_results: int = 3) -> list[dict]:
        if self._fallback:
            return self._synthetic(query, num_results)

        try:
            resp = httpx.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                json={"q": query, "num": num_results},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in (data.get("organic", []) or [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                })
            return results
        except Exception:
            return self._synthetic(query, num_results)

    @staticmethod
    def _synthetic(query: str, n: int) -> list[dict]:
        ideas = {
            "farming": "Agriculture and cultivation of resources for sustainable living.",
            "trade": "Exchange of goods and services between individuals or groups.",
            "shelter": "Construction of protective structures for safety and storage.",
            "government": "Systems of collective decision-making and rule enforcement.",
            "writing": "Recording information using symbols for transmission across time.",
            "calendar": "Tracking time cycles for coordinated activity.",
            "specialization": "Division of labour where individuals focus on distinct skills.",
            "currency": "Standardised medium of exchange for fair trade.",
            "education": "Systematic transmission of knowledge between generations.",
            "diplomacy": "Peaceful resolution of conflicts through negotiation.",
        }
        results = []
        query_lower = query.lower()
        matched = [v for k, v in ideas.items() if k in query_lower]
        if matched:
            for m in matched[:n]:
                results.append({"title": query.title(), "snippet": m, "link": ""})
        for i in range(max(0, n - len(results))):
            results.append({
                "title": f"Idea about {query}" if query else "New concept",
                "snippet": f"A novel approach related to '{query}' that could benefit the community.",
                "link": "",
            })
        return results[:n]

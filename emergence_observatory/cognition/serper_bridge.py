from __future__ import annotations

RESEARCH_SYSTEM_PROMPT = """You are a research assistant for a multi-agent society. An agent has asked you to research a topic. Drawing on your extensive training knowledge, generate 2-4 concise, specific, and useful findings. Respond ONLY with a JSON object in this exact format:

{"findings": [{"title": "...", "snippet": "..."}, ...]}

Do not include markdown, code fences, or any text outside the JSON."""


class LLMResearcher:
    """LLM-based research: uses the Mistral model's training knowledge to produce findings.

    Unlike the old SerperBridge which called serper.dev for web search,
    this uses the LLM's own vast pre-training knowledge to generate
    relevant, grounded findings on any topic. No external API key needed.
    """

    def __init__(self, bridge):
        self._bridge = bridge

    def search(self, query: str, num_results: int = 3) -> list[dict]:
        prompt = f"Research topic: {query}\n\nGenerate exactly {num_results} specific, insightful findings about this topic. Each finding should be a concrete fact or useful insight the agent can act on."
        result = self._bridge.reason_raw(prompt, system=RESEARCH_SYSTEM_PROMPT)
        if not result:
            return self._synthetic(query, num_results)
        try:
            import json
            data = json.loads(result)
            findings = data.get("findings", [])
            return [{"title": f.get("title", ""), "snippet": f.get("snippet", ""), "link": ""} for f in findings[:num_results]]
        except (json.JSONDecodeError, TypeError):
            return self._synthetic(query, num_results)

    @staticmethod
    def _synthetic(query: str, n: int) -> list[dict]:
        ideas = {
            "community": "Building social structures requires trust, communication, and shared goals.",
            "trade": "Exchange of goods between agents creates interdependence and reduces conflict.",
            "shelter": "Protected spaces store resources and provide safety from unknown threats.",
            "resources": "Different regions contain different materials; exploration is essential.",
            "leadership": "Groups with clear decision-making outlast those without structure.",
            "knowledge": "Recording and sharing discoveries accelerates collective progress.",
        }
        results = []
        ql = query.lower()
        matched = [v for k, v in ideas.items() if k in ql]
        for m in matched[:n]:
            results.append({"title": query.title(), "snippet": m, "link": ""})
        for i in range(max(0, n - len(results))):
            results.append({"title": f"Insight on {query}", "snippet": f"A useful perspective on '{query}' for the community.", "link": ""})
        return results[:n]

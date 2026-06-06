from __future__ import annotations
import json
import os
from typing import Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


_STRATEGY_PROMPT = """You are observing a lightweight AI agent in a resource-
gathering simulation. Given the agent's state below, suggest ONE of these
strategies that would best improve its survival:

- "explore"  — move to unexplored areas
- "gather"   — focus on collecting nearby resources
- "social"   — seek communication with other agents
- "rest"     — conserve energy

Respond with a JSON object only:
{{"strategy": "<strategy>", "reasoning": "<brief explanation>"}}

Agent state:
{state}
"""


class DeepSeekBridge:
    """Bridge to an OpenAI-compatible LLM API for structured reasoning.

    Defaults to DeepSeek's public API but can be pointed at any OpenAI-
    compatible endpoint (Ollama, vLLM, llama.cpp, etc.) by setting the
    *base_url*.

    Falls back to deterministic rules when the endpoint is unreachable or
    credentials are missing, so the simulation always runs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
        timeout: float = 10.0,
        env_key: str = "DEEPSEEK_API_KEY",
    ):
        self.api_key = api_key or os.environ.get(env_key)
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._fallback_only = not HAS_HTTPX

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reason(self, agent_state: dict) -> dict | None:
        """Send agent state to the LLM, return ``{"strategy": ..., "reasoning": ...}``."""
        if self._fallback_only:
            return self._fallback(agent_state)

        if not self.api_key and "127.0.0.1" not in self.base_url and "localhost" not in self.base_url:
            return self._fallback(agent_state)

        return self._call_api(agent_state)

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------

    @classmethod
    def ollama(cls, model: str = "deepseek-r1:8b", base_url: str = "http://127.0.0.1:11434/v1"):
        """Convenience constructor for a local Ollama endpoint."""
        return cls(api_key="ollama", model=model, base_url=base_url)

    @classmethod
    def deepseek_api(cls, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        """Convenience constructor for the public DeepSeek API."""
        return cls(api_key=api_key, model=model, base_url="https://api.deepseek.com/v1")

    @classmethod
    def mistral_api(cls, api_key: Optional[str] = None, model: str = "mistral-large-latest"):
        """Convenience constructor for Mistral AI API."""
        return cls(api_key=api_key, model=model, base_url="https://api.mistral.ai/v1", env_key="MISTRAL_API_KEY")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call_api(self, state: dict) -> dict | None:
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "ollama":
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": _STRATEGY_PROMPT.format(state=json.dumps(state))}],
                    "temperature": 0.3,
                    "max_tokens": 150,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_json_response(content)
        except Exception:
            return self._fallback(state)

    @staticmethod
    def _parse_json_response(content: str) -> dict | None:
        """Extract JSON from LLM output, stripping markdown fences if present."""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        return json.loads(cleaned)

    def _fallback(self, state: dict) -> dict:
        energy = state.get("energy", 50)
        strategy = "gather"
        if energy < 20:
            strategy = "gather"
        elif energy > 80 and bool(state.get("inventory", {})):
            strategy = "social"
        elif energy > 60:
            strategy = "explore"
        else:
            strategy = "rest"
        return {"strategy": strategy, "reasoning": "rule-based fallback"}

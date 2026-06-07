from __future__ import annotations
import json
import time
import os
from collections import deque
from typing import Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class RateLimiter:
    """Token-bucket rate limiter for API calls."""

    def __init__(self, calls_per_minute: int = 60):
        self.min_interval = 60.0 / max(calls_per_minute, 1)
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.monotonic()


class MistralBridge:
    """OpenAI-compatible client for Mistral AI API with rate limiting and retry."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistral-large-latest",
        base_url: str = "https://api.mistral.ai/v1",
        rate_limit_rpm: int = 30,
        retry_max: int = 3,
        timeout: float = 20.0,
    ):
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY") or ""
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.retry_max = retry_max
        self.timeout = timeout
        self.rate_limiter = RateLimiter(rate_limit_rpm)
        self.stats = {"calls": 0, "retries": 0, "failures": 0}

    def _chat(self, system_prompt: str, user_prompt: str = "") -> str | None:
        """Low-level chat completion. Returns raw content string or None."""
        for attempt in range(self.retry_max):
            self.rate_limiter.wait()
            try:
                resp = httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt or "What do you do?"},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 300,
                    },
                    timeout=self.timeout,
                )
                self.stats["calls"] += 1
                if resp.status_code == 429:
                    self.stats["retries"] += 1
                    time.sleep(2.0 * (attempt + 1))
                    continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                self.stats["failures"] += 1
                if attempt == self.retry_max - 1:
                    return None
                time.sleep(1.5 * (attempt + 1))
        return None

    def reason(self, system_prompt: str, user_prompt: str = "") -> dict | None:
        """Send a prompt and return the parsed JSON response."""
        content = self._chat(system_prompt, user_prompt)
        return self._parse_json(content) if content else None

    def reason_raw(self, system_prompt: str, user_prompt: str = "") -> str | None:
        """Send a prompt and return the raw string response."""
        return self._chat(system_prompt, user_prompt)

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    @staticmethod
    def _parse_json(content: str) -> dict | None:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

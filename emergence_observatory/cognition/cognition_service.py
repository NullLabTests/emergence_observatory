from __future__ import annotations
from typing import Optional

from .novelty_detector import NoveltyDetector
from .deepseek_bridge import DeepSeekBridge


class CognitionService:
    """Shared cognition service that throttles and routes LLM calls.

    Only agents whose *novelty score* exceeds the threshold trigger an LLM
    reasoning step.  A cooldown period prevents repeated invocations.
    """

    def __init__(self, config):
        self.config = config
        self.novelty_detector = NoveltyDetector()
        self.bridge = self._build_bridge(config)
        self.total_invocations: int = 0
        self.total_fallbacks: int = 0

    def process_event(self, agent_id: int, state_payload: dict) -> dict | None:
        """Send a state payload to the LLM bridge.

        Returns the structured JSON response (strategy recommendation) or
        ``None`` if the request could not be completed.
        """
        result = self.bridge.reason(state_payload)
        self.total_invocations += 1
        if result and result.get("reasoning", "").startswith("rule-based"):
            self.total_fallbacks += 1
        return result

    @staticmethod
    def _build_bridge(config):
        provider = config.llm_provider
        if provider == "ollama":
            return DeepSeekBridge.ollama(model=config.deepseek_model)
        if provider == "deepseek":
            return DeepSeekBridge.deepseek_api(
                api_key=config.deepseek_api_key,
                model=config.deepseek_model,
            )
        if provider == "mistral":
            return DeepSeekBridge.mistral_api(
                api_key=config.deepseek_api_key,
                model=config.deepseek_model,
            )
        return DeepSeekBridge(
            api_key=config.deepseek_api_key,
            model=config.deepseek_model,
            base_url=config.llm_base_url,
        )

    def stats(self) -> dict:
        return {
            "total_invocations": self.total_invocations,
            "total_fallbacks": self.total_fallbacks,
        }

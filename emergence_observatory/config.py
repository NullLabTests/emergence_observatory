from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SimulationConfig:
    world_width: int = 80
    world_height: int = 60
    num_agents: int = 50
    max_agents: int = 200
    max_ticks: int = 5000

    agents_per_tick: int = 3
    tick_interval_ms: int = 1500

    mistral_api_key: Optional[str] = None
    mistral_model: str = "mistral-large-latest"
    llm_rate_limit_rpm: int = 30
    llm_retry_max: int = 3
    llm_timeout: float = 20.0
    llm_enabled: bool = True

    memory_path: str = "data/memory"
    replay_path: str = "data/replay"

    viz_port: int = 5000
    viz_update_interval_ms: int = 2000

    world_seed: int = 42
    personality_seed: int = 42

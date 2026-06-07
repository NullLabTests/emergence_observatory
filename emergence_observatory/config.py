from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SimulationConfig:
    world_width: int = 80
    world_height: int = 60
    num_agents: int = 100
    max_agents: int = 300
    max_ticks: int = 10_000

    agents_per_tick: int = 20
    tick_interval_ms: int = 3000

    mistral_api_key: Optional[str] = None
    mistral_model: str = "mistral-large-latest"
    llm_rate_limit_rpm: int = 120
    llm_retry_max: int = 3
    llm_timeout: float = 20.0
    llm_enabled: bool = True

    memory_path: str = "data/memory"
    replay_path: str = "data/replay"

    viz_port: int = 5000
    viz_update_interval_ms: int = 3000

    world_seed: int = 42
    personality_seed: int = 42

    proposals_enabled: bool = True
    quorum_pct: float = 0.25
    vote_ticks_open: int = 8

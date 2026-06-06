from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SimulationConfig:
    grid_width: int = 100
    grid_height: int = 100
    num_agents: int = 100
    max_agents: int = 1000
    initial_energy: float = 100.0
    energy_cost_per_move: float = 1.0
    energy_gain_per_resource: float = 20.0
    resource_density: float = 0.05
    resource_regeneration_rate: float = 0.01
    max_tick: int = 10_000

    resource_types: list[str] = field(default_factory=lambda: ["food", "water", "stone", "wood"])

    communication_range: int = 15
    max_message_length: int = 100

    short_term_memory_size: int = 10
    long_term_memory_size: int = 200

    llm_enabled: bool = False
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_provider: str = "deepseek"  # "deepseek" | "ollama" | "openai-compat"
    novelty_threshold: float = 0.7
    llm_cooldown_ticks: int = 100

    viz_update_interval_ms: int = 100
    port: int = 5000

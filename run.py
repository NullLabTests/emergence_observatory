#!/usr/bin/env python3
"""Entry point — launch the Emergence Observatory simulation and visualiser."""

from __future__ import annotations
import argparse

from emergence_observatory.config import SimulationConfig
from emergence_observatory.core.simulation import Simulation
from emergence_observatory.viz.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Emergence Observatory")
    parser.add_argument("--agents", type=int, default=100, help="Number of agents")
    parser.add_argument("--width", type=int, default=100, help="Grid width")
    parser.add_argument("--height", type=int, default=100, help="Grid height")
    parser.add_argument("--llm", action="store_true", help="Enable LLM reasoning")
    parser.add_argument("--llm-provider", default="deepseek", choices=["deepseek", "ollama", "openai-compat"],
                        help="LLM backend provider")
    parser.add_argument("--llm-model", default="deepseek-chat", help="LLM model name (e.g. deepseek-chat, deepseek-r1:8b)")
    parser.add_argument("--llm-base-url", default=None, help="Custom base URL for OpenAI-compatible API")
    parser.add_argument("--ollama", action="store_true", help="Shorthand: use Ollama at http://127.0.0.1:11434/v1")
    parser.add_argument("--tick-interval", type=float, default=0.1, help="Seconds between ticks")
    parser.add_argument("--port", type=int, default=5000, help="HTTP port")
    parser.add_argument("--max-tick", type=int, default=10_000, help="Maximum simulation ticks")
    args = parser.parse_args()

    if args.ollama:
        args.llm_provider = "ollama"
        args.llm_model = args.llm_model or "deepseek-r1:8b"

    config = SimulationConfig(
        grid_width=args.width,
        grid_height=args.height,
        num_agents=args.agents,
        max_agents=1000,
        llm_enabled=args.llm or args.ollama,
        deepseek_model=args.llm_model,
        llm_provider=args.llm_provider,
        llm_base_url=args.llm_base_url or "https://api.deepseek.com/v1",
        viz_update_interval_ms=int(args.tick_interval * 1000),
        port=args.port,
        max_tick=args.max_tick,
    )

    sim = Simulation(config)
    app = create_app(sim)

    provider_label = {
        "deepseek": "DeepSeek API",
        "ollama": f"Ollama ({config.deepseek_model})",
        "openai-compat": config.llm_base_url,
    }.get(config.llm_provider, config.llm_provider)

    print(f"  Emergence Observatory — {config.num_agents} agents on {config.grid_width}x{config.grid_height} grid")
    print(f"  LLM: {'ON — ' + provider_label if config.llm_enabled else 'OFF'}")
    print(f"  Dashboard: http://127.0.0.1:{config.port}")
    print("  Press Ctrl+C to stop.\n")

    app.start_simulation()
    try:
        app.run(host="0.0.0.0", port=config.port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        sim.running = False
        sim.logger.close()
        print("\nStopped.")


if __name__ == "__main__":
    main()

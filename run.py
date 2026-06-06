#!/usr/bin/env python3
"""Entry point — Emergence Observatory LLM-native agent laboratory."""

from __future__ import annotations
import argparse
import os

from emergence_observatory.config import SimulationConfig
from emergence_observatory.core.simulation import Simulation
from emergence_observatory.viz.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Emergence Observatory — LLM Agent Laboratory")
    parser.add_argument("--agents", type=int, default=50, help="Number of agents")
    parser.add_argument("--width", type=int, default=80, help="World width")
    parser.add_argument("--height", type=int, default=60, help="World height")
    parser.add_argument("--batch", type=int, default=3, help="Agents acting per tick")
    parser.add_argument("--tick-interval", type=float, default=1.5, help="Seconds between ticks")
    parser.add_argument("--port", type=int, default=5000, help="HTTP port")
    parser.add_argument("--max-ticks", type=int, default=5000, help="Maximum ticks")
    parser.add_argument("--model", default="mistral-large-latest", help="Mistral model name")
    parser.add_argument("--rpm", type=int, default=30, help="LLM rate limit (requests/min)")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM (dry-run)")
    args = parser.parse_args()

    config = SimulationConfig(
        world_width=args.width,
        world_height=args.height,
        num_agents=args.agents,
        max_agents=200,
        max_ticks=args.max_ticks,
        agents_per_tick=args.batch,
        tick_interval_ms=int(args.tick_interval * 1000),
        mistral_api_key=os.environ.get("MISTRAL_API_KEY", ""),
        mistral_model=args.model,
        llm_rate_limit_rpm=args.rpm,
        llm_enabled=not args.no_llm,
        viz_port=args.port,
    )

    sim = Simulation(config)
    app = create_app(sim)

    if not config.mistral_api_key:
        print("  WARNING: MISTRAL_API_KEY not set. LLM calls will fail.")
        print("  Set it with: export MISTRAL_API_KEY='your-key-here'")

    print(f"  Emergence Observatory — LLM Agent Laboratory")
    print(f"  {config.num_agents} agents, {config.world_width}x{config.world_height} world")
    print(f"  {config.agents_per_tick} agents/tick, {config.tick_interval_ms}ms interval")
    print(f"  LLM: {config.mistral_model} @ {config.llm_rate_limit_rpm} RPM")
    print(f"  Dashboard: http://127.0.0.1:{config.port}")
    print("  Press Ctrl+C to stop.\n")

    app.start_simulation()
    try:
        app.run(host="0.0.0.0", port=config.port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        sim.running = False
        sim.recorder.close()
        print("\nStopped.")


if __name__ == "__main__":
    main()

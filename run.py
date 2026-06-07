#!/usr/bin/env python3
"""Entry point — Emergence Observatory: LLM-native society laboratory."""

from __future__ import annotations
import argparse
import os

from emergence_observatory.config import SimulationConfig
from emergence_observatory.core.simulation import Simulation
def main() -> None:
    parser = argparse.ArgumentParser(description="Emergence Observatory — LLM Society Laboratory")
    parser.add_argument("--agents", type=int, default=100, help="Number of agents")
    parser.add_argument("--width", type=int, default=80, help="World width")
    parser.add_argument("--height", type=int, default=60, help="World height")
    parser.add_argument("--batch", type=int, default=10, help="Agents acting per tick")
    parser.add_argument("--tick-interval", type=float, default=2.0, help="Seconds between ticks")
    parser.add_argument("--port", type=int, default=5000, help="HTTP port")
    parser.add_argument("--max-ticks", type=int, default=200, help="Maximum ticks (set 10000 for infinite)")
    parser.add_argument("--model", default="mistral-large-latest", help="Mistral model name")
    parser.add_argument("--rpm", type=int, default=120, help="LLM rate limit (requests/min)")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM (dry-run)")
    parser.add_argument("--no-viz", action="store_true", help="Headless mode (no web server)")
    parser.add_argument("--quorum", type=float, default=0.25, help="Vote quorum fraction")
    parser.add_argument("--vote-ticks", type=int, default=8, help="Ticks before vote closes")
    args = parser.parse_args()

    config = SimulationConfig(
        world_width=args.width,
        world_height=args.height,
        num_agents=args.agents,
        max_agents=300,
        max_ticks=args.max_ticks,
        agents_per_tick=args.batch,
        tick_interval_ms=int(args.tick_interval * 1000),
        mistral_api_key=os.environ.get("MISTRAL_API_KEY", ""),
        mistral_model=args.model,
        llm_rate_limit_rpm=args.rpm,
        llm_enabled=not args.no_llm,
        viz_port=args.port,
        quorum_pct=args.quorum,
        vote_ticks_open=args.vote_ticks,
    )

    sim = Simulation(config)

    if not config.mistral_api_key:
        print("  WARNING: MISTRAL_API_KEY not set. LLM calls will fail.")

    total_calls = config.agents_per_tick * config.max_ticks
    estimated_min = (total_calls / config.llm_rate_limit_rpm) * 1.5 if config.llm_enabled else 0
    print(f"  Emergence Observatory — LLM Society Laboratory")
    print(f"  {config.num_agents} agents on {config.world_width}x{config.world_height} world")
    print(f"  {config.agents_per_tick} agents/tick — est. {total_calls} LLM calls over {config.max_ticks} ticks ({estimated_min:.0f} min)")
    print(f"  LLM: {config.mistral_model} @ {config.llm_rate_limit_rpm} RPM | Research: built-in LLM")
    print(f"  Voting: quorum {config.quorum_pct*100:.0f}%, {config.vote_ticks_open}t open")

    if args.no_viz:
        print("  Headless mode — running without web server.")
        sim.running = True
        try:
            while sim.running and sim.tick < config.max_ticks:
                sim.step()
                if sim.tick % 50 == 0:
                    m = sim.metrics.current()
                    c = sim.cognition.bridge.stats
                    print(f"  tick {sim.tick:5d}: agents={m['num_agents']:3d}  vocab={m['vocab_size']:3d}  "
                          f"allies={m['num_alliances']:2d}  groups={m['num_groups']:2d}  "
                          f"norms={m['passed_norms']:2d}  props={m['open_proposals']:2d}  "
                          f"research={m['total_research']:3d}  votes={m['total_votes']:3d}  "
                          f"llm={c['calls']:4d}", flush=True)
        except KeyboardInterrupt:
            pass
        finally:
            sim.running = False
            sim.recorder.close()
            m = sim.metrics.current()
            c = sim.cognition.bridge.stats
            print(f"\n  === Final (tick {sim.tick}) ===", flush=True)
            for k, v in m.items(): print(f"    {k}: {v}")
            print(f"    llm_calls: {c['calls']} | failures: {c['failures']}", flush=True)
            print(f"    replay: {sim.recorder.path}", flush=True)
    else:
        from emergence_observatory.viz.app import create_app
        print(f"  Dashboard: http://127.0.0.1:{config.port}")
        print("  Press Ctrl+C to stop.\n")
        app = create_app(sim)
        app.start_simulation()
        try:
            app.run(host="0.0.0.0", port=config.port, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            sim.running = False
            sim.recorder.close()
            print("\nStopped.")


if __name__ == "__main__":
    main()

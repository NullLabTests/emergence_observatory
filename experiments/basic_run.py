#!/usr/bin/env python3
"""Basic headless experiment — run N ticks and print final metrics."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emergence_observatory.config import SimulationConfig
from emergence_observatory.core.simulation import Simulation


def main(ticks: int = 200):
    config = SimulationConfig(num_agents=100, grid_width=80, grid_height=80)
    sim = Simulation(config)
    sim.running = True

    for _ in range(ticks):
        sim.step()

    sim.running = False
    print("\n=== Final Metrics ===")
    for k, v in sim.metrics.current().items():
        print(f"  {k}: {v}")
    print(f"\n  Total messages: {sim.comm_system.total_messages}")
    print(f"  Cognition invocations: {sim.cognition.total_invocations}")
    sim.logger.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=200)
    args = parser.parse_args()
    main(args.ticks)

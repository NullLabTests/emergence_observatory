#!/usr/bin/env python3
"""Experiment: compare collective intelligence metrics across agent population sizes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emergence_observatory.config import SimulationConfig
from emergence_observatory.core.simulation import Simulation


def run_experiment(populations: list[int] = (20, 50, 100, 200), ticks: int = 500) -> None:
    results = {}
    for n in populations:
        config = SimulationConfig(num_agents=n, grid_width=100, grid_height=100)
        sim = Simulation(config)
        sim.running = True
        for _ in range(ticks):
            sim.step()
        sim.running = False

        m = sim.metrics.current()
        results[n] = {
            "final_vocab": m["vocab_size"],
            "final_entropy": m["entropy"],
            "graph_density": m["graph_density"],
            "avg_energy": m["avg_energy"],
            "strategy_dist": m["strategy_distribution"],
        }
        sim.logger.close()

    print(f"{'Pop':>6} | {'Vocab':>6} | {'Entropy':>8} | {'GraphDens':>9} | {'AvgE':>6} | {'Dominant strat':>20}")
    print("-" * 70)
    for n, r in results.items():
        dom = max(r["strategy_dist"], key=r["strategy_dist"].get) if r["strategy_dist"] else "?"
        print(f"{n:>6} | {r['final_vocab']:>6} | {r['final_entropy']:>8.3f} | {r['graph_density']:>9.5f} | {r['avg_energy']:>6.1f} | {dom:>20}")


if __name__ == "__main__":
    run_experiment()

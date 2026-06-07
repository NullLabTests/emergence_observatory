#!/usr/bin/env python3
"""Multi-seed experiment runner with structured output.

Usage:
    python experiments/runner.py --name voting_vs_baseline --runs 5 --ticks 30 --agents 30 --batch 10
"""

from __future__ import annotations
import sys, os, json, csv, argparse, time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emergence_observatory.config import SimulationConfig
from emergence_observatory.core.simulation import Simulation
from experiments.novelty_ledger import NoveltyLedger


def run_single_seed(config: SimulationConfig, seed: int, run_dir: Path, label: str) -> dict:
    """Run one simulation seed and return structured summary + write raw data."""
    config.world_seed = seed
    config.personality_seed = seed

    sim = Simulation(config)
    ledger = NoveltyLedger(extinction_delay=10)
    sim.running = True

    seed_dir = run_dir / f"seed_{seed:03d}"
    seed_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = seed_dir / "metrics.jsonl"
    raw_path = seed_dir / "replay.jsonl"

    # Track per-tick metrics ourselves
    tick_data = []

    for t in range(config.max_ticks):
        snap = sim.step()
        m = sim.metrics.current()
        ledger.observe(t, list(sim.agents.values()), governance=label)

        row = {
            "tick": sim.tick,
            "num_agents": m["num_agents"],
            "vocab_size": m["vocab_size"],
            "num_alliances": m["num_alliances"],
            "num_groups": m["num_groups"],
            "passed_norms": m["passed_norms"],
            "open_proposals": m["open_proposals"],
            "total_research": m["total_research"],
            "total_votes": m["total_votes"],
            "avg_energy": m["avg_energy"],
            "graph_density": m["graph_density"],
            "longest_word_survival": m["longest_word_survival"],
        }
        tick_data.append(row)

    sim.running = False
    sim.recorder.close()

    # Write tick-level metrics as CSV
    csv_path = seed_dir / "tick_metrics.csv"
    with open(csv_path, "w", newline="") as f:
        if tick_data:
            w = csv.DictWriter(f, fieldnames=tick_data[0].keys())
            w.writeheader()
            w.writerows(tick_data)

    # Write novelty ledger
    ledger_path = seed_dir / "novelty_ledger.json"
    with open(ledger_path, "w") as f:
        json.dump(ledger.summary(), f, indent=2)

    # Compute final summary
    last = tick_data[-1] if tick_data else {}
    ledger_summary = ledger.summary()
    return {
        "seed": seed,
        "label": label,
        "tick": sim.tick,
        "llm_calls": sim.cognition.bridge.stats["calls"],
        "llm_failures": sim.cognition.bridge.stats["failures"],
        **last,
        "total_words_invented": ledger_summary.get("total_words_invented", 0),
        "alive_words": ledger_summary.get("alive_words", 0),
        "extinct_words": ledger_summary.get("extinct_words", 0),
        "mean_word_lifetime": ledger_summary.get("mean_lifetime_ticks", 0),
        "median_word_lifetime": ledger_summary.get("median_lifetime_ticks", 0),
        "max_word_lifetime": ledger_summary.get("max_lifetime_ticks", 0),
        "max_peak_adoption": ledger_summary.get("max_peak_adoption", 0),
    }


def run_experiment(
    name: str = "experiment",
    runs: int = 5,
    ticks: int = 30,
    agents: int = 30,
    batch: int = 10,
    rpm: int = 300,
    seeds: list[int] | None = None,
    api_key: str = "",
) -> None:
    base = Path(__file__).resolve().parent / name
    base.mkdir(parents=True, exist_ok=True)

    if seeds is None:
        seeds = list(range(1, runs + 1))

    configs = []

    # Baseline: no voting (vote_ticks_open very high so proposals never close)
    configs.append(("baseline", SimulationConfig(
        num_agents=agents, world_width=50, world_height=40,
        agents_per_tick=batch, max_ticks=ticks,
        llm_rate_limit_rpm=rpm, vote_ticks_open=9999,
        mistral_api_key=api_key, llm_enabled=True,
    )))

    # Voting enabled
    configs.append(("voting", SimulationConfig(
        num_agents=agents, world_width=50, world_height=40,
        agents_per_tick=batch, max_ticks=ticks,
        llm_rate_limit_rpm=rpm, vote_ticks_open=6, quorum_pct=0.25,
        mistral_api_key=api_key, llm_enabled=True,
    )))

    all_results: dict[str, list[dict]] = {"baseline": [], "voting": []}

    for label, config in configs:
        print(f"\n  Condition: {label}", flush=True)
        cond_dir = base / label
        cond_dir.mkdir(parents=True, exist_ok=True)

        for seed in seeds:
            t0 = time.time()
            print(f"    seed {seed}...", end=" ", flush=True)
            result = run_single_seed(config, seed, cond_dir, label)
            elapsed = time.time() - t0
            print(f"done ({elapsed:.0f}s) — tick {result['tick']}, vocab {result['vocab_size']}, "
                  f"words invented {result['total_words_invented']}, llm {result['llm_calls']}", flush=True)
            all_results[label].append(result)

    # Write aggregate summary CSV
    for label, results in all_results.items():
        csv_path = base / label / "summary.csv"
        with open(csv_path, "w", newline="") as f:
            if results:
                w = csv.DictWriter(f, fieldnames=results[0].keys())
                w.writeheader()
                w.writerows(results)

    # Write comparison summary with statistics
    comp_path = base / "comparison.json"
    comparison = {}
    for label, results in all_results.items():
        if not results:
            continue
        keys = [k for k in results[0].keys() if k not in ("seed", "label")]
        stats = {}
        n = len(results)
        for k in keys:
            vals = [r[k] for r in results if isinstance(r[k], (int, float))]
            if not vals:
                continue
            mean = sum(vals) / n
            variance = sum((v - mean) ** 2 for v in vals) / n
            std = variance ** 0.5
            ci95 = 1.96 * std / (n ** 0.5)
            stats[k] = {
                "mean": round(mean, 2),
                "std": round(std, 2),
                "ci95": round(ci95, 2),
                "min": round(min(vals), 2),
                "max": round(max(vals), 2),
            }
        comparison[label] = {"runs": n, "stats": stats}

    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"\n  === Comparison ===", flush=True)
    for label, data in comparison.items():
        print(f"  [{label}] {data['runs']} runs", flush=True)
        for k, s in data["stats"].items():
            if k in ("vocab_size", "total_words_invented", "passed_norms", "num_alliances", "total_votes", "total_research", "mean_word_lifetime", "max_word_lifetime", "llm_calls", "llm_failures"):
                print(f"    {k}: {s['mean']} ± {s['ci95']} (std={s['std']}) [{s['min']}–{s['max']}]", flush=True)
        print(flush=True)

    print(f"\n  Data: {base}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="voting_vs_baseline")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--ticks", type=int, default=50)
    parser.add_argument("--agents", type=int, default=20)
    parser.add_argument("--batch", type=int, default=10)
    parser.add_argument("--rpm", type=int, default=300)
    args = parser.parse_args()

    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        sys.exit(1)

    run_experiment(
        name=args.name,
        runs=args.runs,
        ticks=args.ticks,
        agents=args.agents,
        batch=args.batch,
        rpm=args.rpm,
        api_key=api_key,
    )

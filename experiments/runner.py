#!/usr/bin/env python3
"""Multi-seed experiment runner with structured output.

Usage:
    python experiments/runner.py --name three_conditions --runs 10 --ticks 50 --agents 20 --batch 10
"""

from __future__ import annotations
import sys, os, json, csv, argparse, time, math, random
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emergence_observatory.config import SimulationConfig
from emergence_observatory.core.simulation import Simulation
from experiments.novelty_ledger import NoveltyLedger
from experiments.semantic_drift import DriftRecorder


def run_single_seed(config: SimulationConfig, seed: int, run_dir: Path, label: str) -> dict:
    """Run one simulation seed and return structured summary + write raw data."""
    config.world_seed = seed
    config.personality_seed = seed

    sim = Simulation(config)
    ledger = NoveltyLedger(extinction_delay=10)
    drift = DriftRecorder()
    sim.running = True

    seed_dir = run_dir / f"seed_{seed:03d}"
    seed_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = seed_dir / "metrics.jsonl"
    raw_path = seed_dir / "replay.jsonl"

    tick_data = []

    for t in range(config.max_ticks):
        snap = sim.step()
        m = sim.metrics.current()
        ledger.observe(t, list(sim.agents.values()), governance=label)
        drift.observe(t, list(sim.agents.values()))

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

    csv_path = seed_dir / "tick_metrics.csv"
    with open(csv_path, "w", newline="") as f:
        if tick_data:
            w = csv.DictWriter(f, fieldnames=tick_data[0].keys())
            w.writeheader()
            w.writerows(tick_data)

    ledger_path = seed_dir / "novelty_ledger.json"
    with open(ledger_path, "w") as f:
        json.dump(ledger.summary(), f, indent=2)

    drift_path = seed_dir / "drift_snapshots.json"
    drift.save(drift_path)

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


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def compute_stats(vals: list[float]) -> dict:
    n = len(vals)
    if n == 0:
        return {}
    mean = sum(vals) / n
    variance = sum((v - mean) ** 2 for v in vals) / n
    std = variance ** 0.5
    ci95 = 1.96 * std / (n ** 0.5) if n > 0 else 0
    return {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "ci95": round(ci95, 4),
        "min": round(min(vals), 4),
        "max": round(max(vals), 4),
        "n": n,
    }


def bootstrap_ci(values: list[float], n_resamples: int = 10000, alpha: float = 0.05) -> dict:
    """Percentile bootstrap confidence interval for the mean."""
    if len(values) < 3:
        return compute_stats(values)
    means = []
    rng = random.Random(42)
    for _ in range(n_resamples):
        sample = [rng.choice(values) for _ in range(len(values))]
        means.append(sum(sample) / len(sample))
    means.sort()
    low_idx = int((alpha / 2) * n_resamples)
    high_idx = int((1 - alpha / 2) * n_resamples)
    return {
        "mean": round(sum(values) / len(values), 4),
        "ci95_low": round(means[low_idx], 4),
        "ci95_high": round(means[high_idx], 4),
        "std": round(compute_stats(values)["std"], 4),
        "n": len(values),
    }


def mann_whitney_u(x: list[float], y: list[float]) -> dict:
    """Mann-Whitney U test with normal approximation."""
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return {"U": None, "p_value": None, "nx": nx, "ny": ny}

    combined = [(val, 0) for val in x] + [(val, 1) for val in y]
    combined.sort(key=lambda p: p[0])
    n = len(combined)
    ranks = {}
    i = 0
    while i < n:
        j = i
        while j < n and combined[j][0] == combined[i][0]:
            j += 1
        rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[k] = rank
        i = j

    r1 = sum(ranks[k] for k in range(n) if combined[k][1] == 0)
    u1 = r1 - nx * (nx + 1) / 2
    u2 = nx * ny - u1
    u_stat = min(u1, u2)

    mu = nx * ny / 2
    sigma = math.sqrt(nx * ny * (nx + ny + 1) / 12)
    if sigma == 0:
        return {"U": u_stat, "p_value": 1.0, "nx": nx, "ny": ny}
    z = (u_stat - mu) / sigma
    p_value = 2 * (1 - _normal_cdf(abs(z)))
    return {"U": round(u_stat, 2), "p_value": round(p_value, 4), "z": round(z, 4), "nx": nx, "ny": ny}


def _normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ---------------------------------------------------------------------------
# Condition definitions
# ---------------------------------------------------------------------------

def make_conditions(agents: int, ticks: int, batch: int, rpm: int, api_key: str) -> list[tuple[str, SimulationConfig]]:
    return [
        ("no_proposals", SimulationConfig(
            num_agents=agents, world_width=50, world_height=40,
            agents_per_tick=batch, max_ticks=ticks,
            llm_rate_limit_rpm=rpm, proposals_enabled=False,
            mistral_api_key=api_key, llm_enabled=True,
        )),
        ("baseline", SimulationConfig(
            num_agents=agents, world_width=50, world_height=40,
            agents_per_tick=batch, max_ticks=ticks,
            llm_rate_limit_rpm=rpm, vote_ticks_open=9999,
            mistral_api_key=api_key, llm_enabled=True,
        )),
        ("voting", SimulationConfig(
            num_agents=agents, world_width=50, world_height=40,
            agents_per_tick=batch, max_ticks=ticks,
            llm_rate_limit_rpm=rpm, vote_ticks_open=6, quorum_pct=0.25,
            mistral_api_key=api_key, llm_enabled=True,
        )),
    ]


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------

def run_experiment(
    name: str = "three_conditions",
    runs: int = 10,
    ticks: int = 50,
    agents: int = 20,
    batch: int = 10,
    rpm: int = 300,
    seeds: list[int] | None = None,
    api_key: str = "",
) -> None:
    base = Path(__file__).resolve().parent / name
    base.mkdir(parents=True, exist_ok=True)

    if seeds is None:
        seeds = list(range(1, runs + 1))

    configs = make_conditions(agents, ticks, batch, rpm, api_key)
    all_results: dict[str, list[dict]] = {label: [] for label, _ in configs}

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

    # Write per-condition summary CSVs
    for label, results in all_results.items():
        csv_path = base / label / "summary.csv"
        with open(csv_path, "w", newline="") as f:
            if results:
                w = csv.DictWriter(f, fieldnames=results[0].keys())
                w.writeheader()
                w.writerows(results)

    # Compute stats with bootstrap
    comparison = {}
    for label, results in all_results.items():
        if not results:
            continue
        keys = [k for k in results[0].keys() if k not in ("seed", "label")]
        stats = {}
        for k in keys:
            vals = [r[k] for r in results if isinstance(r[k], (int, float))]
            if not vals:
                continue
            stats[k] = bootstrap_ci(vals)
        comparison[label] = {"runs": len(results), "stats": stats}

    # Between-condition Mann-Whitney U tests
    labels = [label for label, _ in configs]
    comparisons = {}
    for i, la in enumerate(labels):
        for j, lb in enumerate(labels):
            if j <= i:
                continue
            key = f"{la}_vs_{lb}"
            comparisons[key] = {}
            metric_keys = ["vocab_size", "total_words_invented", "mean_word_lifetime",
                           "max_word_lifetime", "passed_norms", "total_votes",
                           "num_alliances", "num_groups", "total_research"]
            for k in metric_keys:
                x = [r[k] for r in all_results[la] if isinstance(r[k], (int, float))]
                y = [r[k] for r in all_results[lb] if isinstance(r[k], (int, float))]
                if len(x) >= 2 and len(y) >= 2:
                    comparisons[key][k] = mann_whitney_u(x, y)
    comparison["between_condition_tests"] = comparisons

    comp_path = base / "comparison.json"
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2)

    # Print summary
    print(f"\n  === Comparison ===", flush=True)
    for label, data in comparison.items():
        if label == "between_condition_tests":
            continue
        print(f"  [{label}] {data['runs']} runs", flush=True)
        for k, s in data["stats"].items():
            if k in ("vocab_size", "total_words_invented", "passed_norms", "num_alliances",
                     "total_votes", "total_research", "mean_word_lifetime",
                     "max_word_lifetime", "llm_calls", "llm_failures"):
                ci = f" [{s['ci95_low']}–{s['ci95_high']}]" if 'ci95_low' in s else ""
                print(f"    {k}: {s['mean']}{ci} "
                      f"std={s['std']}  n={s['n']}", flush=True)
        print(flush=True)

    if comparisons:
        print("  Between-condition Mann-Whitney U tests:", flush=True)
        for key, tests in comparisons.items():
            print(f"    {key}:", flush=True)
            for metric, res in tests.items():
                if res["p_value"] is not None:
                    sig = " ***" if res["p_value"] < 0.001 else " **" if res["p_value"] < 0.01 else " *" if res["p_value"] < 0.05 else ""
                    print(f"      {metric}: U={res['U']}, p={res['p_value']}{sig}", flush=True)
        print(flush=True)

    print(f"\n  Data: {base}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="three_conditions")
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

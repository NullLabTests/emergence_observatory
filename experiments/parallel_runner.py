#!/usr/bin/env python3
"""Multi-process experiment runner — runs seeds in parallel across CPU cores.

Usage:
    python experiments/parallel_runner.py --name three_conditions --runs 10 --ticks 50 --workers 4
"""

from __future__ import annotations
import sys, os, json, csv, argparse, time, math, random
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from emergence_observatory.config import SimulationConfig
from experiments.runner import run_single_seed, make_conditions, bootstrap_ci, mann_whitney_u


def run_seed_worker(args: tuple) -> dict:
    """Wrapper for run_single_seed that unpacks a tuple (needed for pickling)."""
    config, seed, run_dir, label = args
    return run_single_seed(config, seed, run_dir, label)


def run_experiment_parallel(
    name: str = "three_conditions",
    runs: int = 10,
    ticks: int = 50,
    agents: int = 20,
    batch: int = 10,
    rpm: int = 300,
    workers: int = 2,
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
        print(f"\n  Condition: {label} (parallel, {workers} workers)", flush=True)
        cond_dir = base / label
        cond_dir.mkdir(parents=True, exist_ok=True)

        tasks = [(config, seed, cond_dir, label) for seed in seeds]

        t0 = time.time()
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(run_seed_worker, t): t[1] for t in tasks}
            for future in as_completed(futures):
                seed = futures[future]
                try:
                    result = future.result()
                    elapsed = time.time() - t0
                    print(f"    seed {seed} done ({elapsed:.0f}s) — tick {result['tick']}, "
                          f"vocab {result['vocab_size']}, words {result['total_words_invented']}, "
                          f"llm {result['llm_calls']}", flush=True)
                    all_results[label].append(result)
                except Exception as e:
                    print(f"    seed {seed} FAILED: {e}", flush=True)

        cond_elapsed = time.time() - t0
        print(f"  [{label}] {len(all_results[label])} seeds completed in {cond_elapsed:.0f}s", flush=True)

    # Write per-condition summary CSVs
    for label, results in all_results.items():
        csv_path = base / label / "summary.csv"
        with open(csv_path, "w", newline="") as f:
            if results:
                w = csv.DictWriter(f, fieldnames=results[0].keys())
                w.writeheader()
                w.writerows(results)

    # Stats with bootstrap
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
    parser = argparse.ArgumentParser(description="Parallel multi-seed experiment runner")
    parser.add_argument("--name", default="three_conditions")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--ticks", type=int, default=50)
    parser.add_argument("--agents", type=int, default=20)
    parser.add_argument("--batch", type=int, default=10)
    parser.add_argument("--rpm", type=int, default=300)
    parser.add_argument("--workers", "-w", type=int, default=2,
                        help="Number of parallel worker processes (default: 2)")
    args = parser.parse_args()

    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        sys.exit(1)

    run_experiment_parallel(
        name=args.name,
        runs=args.runs,
        ticks=args.ticks,
        agents=args.agents,
        batch=args.batch,
        rpm=args.rpm,
        workers=args.workers,
        api_key=api_key,
    )

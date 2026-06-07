#!/usr/bin/env python3
"""Linguistic analysis for invented vocabulary across experiment conditions.

Computes:
  - Zipf α: power-law exponent of rank-frequency distribution of invented words
  - Heaps β: type-token growth exponent (vocab_size ~ tokens^β)
  - Per-condition summary with bootstrap CIs
  - Mann-Whitney U tests between conditions

Usage:
    python experiments/linguistic_analysis.py --experiment-dir experiments/voting_vs_baseline
"""

from __future__ import annotations
import sys, json, csv, math, argparse, random
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_seed_data(seed_dir: Path) -> tuple[list[dict], dict]:
    """Load tick_metrics.csv and novelty_ledger.json for one seed."""
    csv_path = seed_dir / "tick_metrics.csv"
    ledger_path = seed_dir / "novelty_ledger.json"
    ticks = []
    if csv_path.exists():
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticks.append({k: _try_float(v) for k, v in row.items()})
    ledger = {}
    if ledger_path.exists():
        with open(ledger_path) as f:
            ledger = json.load(f)
    return ticks, ledger


def _try_float(v: str) -> float | str:
    try:
        return float(v)
    except (ValueError, TypeError):
        return v


def compute_zipf(word_counts: dict[str, int]) -> float | None:
    """Fit power-law to rank-frequency distribution, return exponent α.

    Uses log-log linear regression: log(freq) ~ α * log(rank).
    Higher α = steeper drop-off (fewer high-frequency words).
    """
    if len(word_counts) < 3:
        return None
    sorted_counts = sorted(word_counts.values(), reverse=True)
    ranks = list(range(1, len(sorted_counts) + 1))
    n = len(sorted_counts)
    log_rank = [math.log(r) for r in ranks]
    log_freq = [math.log(max(c, 1e-9)) for c in sorted_counts]

    mean_x = sum(log_rank) / n
    mean_y = sum(log_freq) / n
    num = sum((log_rank[i] - mean_x) * (log_freq[i] - mean_y) for i in range(n))
    den = sum((log_rank[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return None
    return round(num / den, 4)


def compute_heaps(tick_vocab_sizes: list[int]) -> float | None:
    """Fit vocab_size ~ tokens^β, return exponent β.

    β < 1 indicates sublinear growth (vocabulary saturates).
    β near 1 indicates novel tokens appear at constant rate.
    """
    if len(tick_vocab_sizes) < 4:
        return None
    tokens = list(range(1, len(tick_vocab_sizes) + 1))
    n = len(tick_vocab_sizes)
    log_tokens = [math.log(t) for t in tokens]
    log_vocab = [math.log(max(v, 1)) for v in tick_vocab_sizes]

    mean_x = sum(log_tokens) / n
    mean_y = sum(log_vocab) / n
    num = sum((log_tokens[i] - mean_x) * (log_vocab[i] - mean_y) for i in range(n))
    den = sum((log_tokens[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return None
    return round(num / den, 4)


def analyze_condition(cond_dir: Path, label: str) -> dict:
    """Analyze all seeds in one condition directory."""
    seed_dirs = sorted([d for d in cond_dir.iterdir() if d.is_dir() and d.name.startswith("seed_")])
    seeds = []
    for sd in seed_dirs:
        ticks, ledger = load_seed_data(sd)
        if not ticks:
            continue
        word_counts = {}
        all_vocab_sizes = [t.get("vocab_size", 0) for t in ticks]

        # Build per-tick word frequency for final Zipf
        words = ledger.get("words", [])
        for w in words:
            word_counts[w.get("word", "?")] = w.get("peak_adoption", 1)

        zipf_alpha = compute_zipf(word_counts)
        heaps_beta = compute_heaps(all_vocab_sizes)

        seeds.append({
            "seed": int(sd.name.split("_")[1]),
            "final_vocab": all_vocab_sizes[-1] if all_vocab_sizes else 0,
            "total_words_invented": ledger.get("total_words_invented", 0),
            "alive_words": ledger.get("alive_words", 0),
            "extinct_words": ledger.get("extinct_words", 0),
            "mean_word_lifetime": ledger.get("mean_lifetime_ticks", 0),
            "zipf_alpha": zipf_alpha,
            "heaps_beta": heaps_beta,
            "max_peak_adoption": ledger.get("max_peak_adoption", 0),
        })

    if not seeds:
        return {"label": label, "seeds": [], "stats": {}}

    keys = ["final_vocab", "total_words_invented", "alive_words", "extinct_words",
            "mean_word_lifetime", "zipf_alpha", "heaps_beta", "max_peak_adoption"]
    stats = {}
    n = len(seeds)
    for k in keys:
        vals = [s[k] for s in seeds if s[k] is not None]
        if not vals:
            continue
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = variance ** 0.5
        ci95 = 1.96 * std / (len(vals) ** 0.5)
        stats[k] = {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "ci95": round(ci95, 4),
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
        }
    return {"label": label, "seeds": seeds, "stats": stats}


def mann_whitney_u(x: list[float], y: list[float]) -> dict:
    """Compute Mann-Whitney U test between two samples.

    Returns U statistic and approximate p-value (normal approximation).
    """
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return {"U": None, "p_value": None, "nx": nx, "ny": ny}

    combined = [(val, 0) for val in x] + [(val, 1) for val in y]
    combined.sort(key=lambda p: p[0])
    ranks = {}
    i = 0
    n = len(combined)
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


def bootstrap_ci(values: list[float], n_resamples: int = 10000, ci: float = 0.95) -> dict:
    """Compute bootstrap percentile confidence interval for the mean."""
    if len(values) < 2:
        return {"mean": None, "ci_low": None, "ci_high": None, "n": len(values)}
    means = []
    rng = random.Random(42)
    for _ in range(n_resamples):
        sample = [rng.choice(values) for _ in range(len(values))]
        means.append(sum(sample) / len(sample))
    means.sort()
    alpha = (1 - ci) / 2
    low_idx = int(alpha * n_resamples)
    high_idx = int((1 - alpha) * n_resamples)
    return {
        "mean": round(sum(values) / len(values), 4),
        "ci_low": round(means[low_idx], 4),
        "ci_high": round(means[high_idx], 4),
        "n": len(values),
    }


def main():
    parser = argparse.ArgumentParser(description="Linguistic analysis of invented vocabulary")
    parser.add_argument("--experiment-dir", "-d", default="experiments/voting_vs_baseline",
                        help="Path to experiment directory containing condition subdirs")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON path (default: <experiment_dir>/linguistic_analysis.json)")
    parser.add_argument("--bootstrap", type=int, default=10000,
                        help="Number of bootstrap resamples (default: 10000)")
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    if not exp_dir.is_dir():
        print(f"ERROR: experiment directory not found: {exp_dir}")
        sys.exit(1)

    conditions = []
    for child in sorted(exp_dir.iterdir()):
        if child.is_dir() and child.name != "__pycache__":
            result = analyze_condition(child, child.name)
            if result["seeds"]:
                conditions.append(result)

    if not conditions:
        print("ERROR: no condition directories found")
        sys.exit(1)

    output = {"experiment_dir": str(exp_dir), "conditions": {}}
    for cond in conditions:
        label = cond["label"]
        output["conditions"][label] = {
            "stats": cond["stats"],
            "seeds": cond["seeds"],
        }

        # Per-seed detail
        for k in ("zipf_alpha", "heaps_beta"):
            vals = [s[k] for s in cond["seeds"] if s[k] is not None]
            output["conditions"][label][f"{k}_bootstrap"] = bootstrap_ci(vals, n_resamples=args.bootstrap)

    # Between-condition tests
    comparisons = {}
    for i, ca in enumerate(conditions):
        for j, cb in enumerate(conditions):
            if j <= i:
                continue
            key = f"{ca['label']}_vs_{cb['label']}"
            comparisons[key] = {}
            for metric in ("final_vocab", "total_words_invented", "mean_word_lifetime",
                           "zipf_alpha", "heaps_beta", "max_peak_adoption"):
                x = [s[metric] for s in ca["seeds"] if s[metric] is not None]
                y = [s[metric] for s in cb["seeds"] if s[metric] is not None]
                if len(x) >= 2 and len(y) >= 2:
                    comparisons[key][metric] = mann_whitney_u(x, y)
    output["comparisons"] = comparisons

    out_path = args.output or (exp_dir / "linguistic_analysis.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Linguistic analysis saved to {out_path}\n", flush=True)

    # Print summary
    for label, data in output["conditions"].items():
        s = data["stats"]
        print(f"  [{label}]")
        for k in ("final_vocab", "total_words_invented", "mean_word_lifetime",
                  "zipf_alpha", "heaps_beta"):
            if k in s:
                print(f"    {k}: {s[k]['mean']} ±{s[k]['ci95']} [{s[k]['min']}–{s[k]['max']}]")
        print()

    if comparisons:
        print("  Between-condition tests (Mann-Whitney U):")
        for key, tests in comparisons.items():
            print(f"    {key}:")
            for metric, result in tests.items():
                if result["p_value"] is not None:
                    sig = " ***" if result["p_value"] < 0.001 else " **" if result["p_value"] < 0.01 else " *" if result["p_value"] < 0.05 else ""
                    print(f"      {metric}: U={result['U']}, p={result['p_value']}{sig}")
        print()


if __name__ == "__main__":
    main()

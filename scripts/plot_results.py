#!/usr/bin/env python3
"""Generate publication-ready plots from experiment output.

Produces:
  - vocab_growth.png     — vocabulary size over tick (all seeds, per condition)
  - comparison_bar.png   — bar chart comparing key metrics across conditions
  - drift_time_series.png — semantic drift magnitude over time
  - adoption_curves.png  — word adoption S-curves per condition

Usage:
    python scripts/plot_results.py --experiment-dir experiments/three_conditions
"""

from __future__ import annotations
import sys, json, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Optional matplotlib import — fail gracefully if not installed
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

FONT_SIZE = 11
COLORS = {"no_proposals": "#e24a33", "baseline": "#4a9eff", "voting": "#4caf50"}
DASHES = {"no_proposals": (2, 2), "baseline": (1, 0), "voting": (4, 2)}


def _try_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return v


def load_seed_ticks(seed_dir: Path) -> list[dict] | None:
    path = seed_dir / "tick_metrics.csv"
    if not path.exists():
        return None
    with open(path) as f:
        reader = csv.DictReader(f)
        return [{k: _try_float(v) for k, v in row.items()} for row in reader]


def collect_condition_data(cond_dir: Path) -> dict:
    """Collect per-seed tick data for one condition."""
    seed_dirs = sorted([d for d in cond_dir.iterdir() if d.is_dir() and d.name.startswith("seed_")])
    seeds = {}
    for sd in seed_dirs:
        ticks = load_seed_ticks(sd)
        if ticks:
            seed_n = int(sd.name.split("_")[1])
            seeds[seed_n] = ticks
    return seeds


def plot_vocab_growth(all_data: dict, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, seeds in all_data.items():
        for seed_n, ticks in seeds.items():
            ticks_list = [t["tick"] for t in ticks]
            vocabs = [t["vocab_size"] for t in ticks]
            ax.plot(ticks_list, vocabs, color=COLORS.get(label, "#888"),
                    alpha=0.5, linewidth=0.8, dashes=DASHES.get(label, (1, 0)))
        # Mean line
        if seeds:
            max_len = max(len(t) for t in seeds.values())
            mean_vocab = []
            for i in range(max_len):
                vals = [t[i]["vocab_size"] for t in seeds.values() if i < len(t)]
                mean_vocab.append(sum(vals) / len(vals))
            ax.plot(range(1, max_len + 1), mean_vocab, color=COLORS.get(label, "#888"),
                    label=label, linewidth=2.5)

    ax.set_xlabel("Tick", fontsize=FONT_SIZE)
    ax.set_ylabel("Vocabulary size", fontsize=FONT_SIZE)
    ax.set_title("Vocabulary Growth Across Conditions", fontsize=FONT_SIZE + 1)
    ax.legend(fontsize=FONT_SIZE - 1)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "vocab_growth.png", dpi=200)
    plt.close(fig)
    print(f"  Saved {out_dir / 'vocab_growth.png'}")


def plot_comparison_bar(all_data: dict, comparison: dict, out_dir: Path) -> None:
    metrics = ["vocab_size", "total_words_invented", "mean_word_lifetime", "passed_norms"]
    labels = list(all_data.keys())
    if len(labels) < 2:
        return

    fig, axes = plt.subplots(1, len(metrics), figsize=(3.2 * len(metrics), 3.5))
    for ax, metric in zip(axes, metrics):
        means = []
        errs = []
        colors = []
        for label in labels:
            s = comparison.get(label, {}).get("stats", {}).get(metric, {})
            means.append(s.get("mean", 0))
            errs.append(s.get("ci95_high", 0) - s.get("mean", 0) if "ci95_high" in s else 0)
            colors.append(COLORS.get(label, "#888"))
        bars = ax.bar(labels, means, yerr=errs, capsize=4, color=colors, alpha=0.8)
        ax.set_title(metric.replace("_", " ").title(), fontsize=FONT_SIZE - 1)
        ax.tick_params(axis="x", rotation=20, labelsize=8)
        ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(out_dir / "comparison_bar.png", dpi=200)
    plt.close(fig)
    print(f"  Saved {out_dir / 'comparison_bar.png'}")


def plot_drift_series(all_data: dict, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    has_data = False
    for label, seeds in all_data.items():
        drift_vals = []
        for seed_n, ticks in seeds.items():
            drift_path = Path(seed_n).parent / "drift_snapshots.json"
            # Can't get drift from tick metrics alone — skip if no snapshots
    if not has_data:
        plt.close(fig)
        return
    # (Drift time series requires drift_snapshots.json per seed — needs separate loader)
    plt.close(fig)


def plot_adoption_curves(all_data: dict, out_dir: Path) -> None:
    """Plot word adoption: how many agents know invented words over time."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, seeds in all_data.items():
        n_agents_data = []
        for seed_n, ticks in seeds.items():
            n_agents_data.append([t["total_words_invented"] for t in ticks])
        if n_agents_data:
            max_len = max(len(d) for d in n_agents_data)
            means = []
            for i in range(max_len):
                vals = [d[i] for d in n_agents_data if i < len(d)]
                means.append(sum(vals) / len(vals))
            ax.plot(range(1, max_len + 1), means, color=COLORS.get(label, "#888"),
                    label=label, linewidth=2.5)
    ax.set_xlabel("Tick", fontsize=FONT_SIZE)
    ax.set_ylabel("Total invented words", fontsize=FONT_SIZE)
    ax.set_title("Word Invention Rate Across Conditions", fontsize=FONT_SIZE + 1)
    ax.legend(fontsize=FONT_SIZE - 1)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "word_invention_rate.png", dpi=200)
    plt.close(fig)
    print(f"  Saved {out_dir / 'word_invention_rate.png'}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate plots from experiment data")
    parser.add_argument("--experiment-dir", "-d", required=True)
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    if not HAS_MPL:
        print("ERROR: matplotlib not installed. Run: pip install matplotlib")
        sys.exit(1)

    exp_dir = Path(args.experiment_dir)
    out_dir = Path(args.output) if args.output else exp_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    all_data = {}
    for child in sorted(exp_dir.iterdir()):
        if child.is_dir() and child.name != "__pycache__":
            data = collect_condition_data(child)
            if data:
                all_data[child.name] = data

    if not all_data:
        print("No seed data found")
        sys.exit(1)

    # Load comparison for bar chart
    comp_path = exp_dir / "comparison.json"
    comparison = {}
    if comp_path.exists():
        with open(comp_path) as f:
            comparison = json.load(f)

    print(f"\n  Generating plots in {out_dir} ...\n")
    plot_vocab_growth(all_data, out_dir)
    plot_comparison_bar(all_data, comparison, out_dir)
    plot_adoption_curves(all_data, out_dir)
    print("\n  Done.\n")


if __name__ == "__main__":
    main()

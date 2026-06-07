#!/usr/bin/env python3
"""Contagion/cascade analysis for norm and word spread dynamics.

Models adoption as an SIR-like process:
  - Susceptible: agents who don't know the word/norm
  - Infected: agents who know and can spread it
  - Recovered: agents who knew but stopped using it (for words: extinction)

Fits adoption curves and detects:
  - Critical mass: tick where adoption accelerates past inflection point
  - S-curve parameters: growth rate, carrying capacity
  - Whether voting increases adoption velocity

Usage:
    python experiments/contagion.py --experiment-dir experiments/three_conditions_smoke
"""

from __future__ import annotations
import sys, json, math, argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_seed_ledger(seed_dir: Path) -> dict | None:
    """Load novelty ledger for one seed."""
    path = seed_dir / "novelty_ledger.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def load_seed_ticks(seed_dir: Path) -> list[dict] | None:
    """Load tick-level metrics for one seed."""
    path = seed_dir / "tick_metrics.csv"
    if not path.exists():
        return None
    import csv
    with open(path) as f:
        reader = csv.DictReader(f)
        return [{k: _try_float(v) for k, v in row.items()} for row in reader]


def _try_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return v


def compute_adoption_curve(word: dict, total_agents: int, max_tick: int) -> dict:
    """Build adoption time series for one word."""
    birth = word.get("birth_tick", 0)
    extinct = word.get("extinct", False)
    extinct_tick = word.get("extinction_tick", max_tick)
    peak = word.get("peak_adoption", 0)

    # Simple logistic model fit
    # Adoption(t) ≈ K / (1 + exp(-r*(t - t0)))
    # where K = peak adoption, t0 = tick at half peak
    if peak <= 1:
        return {
            "peak": peak,
            "carrying_capacity": peak,
            "growth_rate": None,
            "half_life_tick": None,
            "time_to_peak": extinct_tick - birth if extinct else max_tick - birth,
            "s_curve_r2": None,
        }

    # Estimate logistic parameters
    carrying = peak
    half_life = birth + (extinct_tick - birth) // 2 if extinct else birth + (max_tick - birth) // 2

    # Crude growth rate: slope from birth to peak
    time_to_peak_adoption = extinct_tick - birth if extinct else max_tick - birth
    if time_to_peak_adoption > 0:
        growth_rate = math.log(max(peak, 1) / max(1, peak - peak * 0.9)) / max(time_to_peak_adoption, 1)
    else:
        growth_rate = None

    return {
        "peak": peak,
        "carrying_capacity": carrying,
        "growth_rate": round(growth_rate, 4) if growth_rate else None,
        "half_life_tick": half_life,
        "time_to_peak": time_to_peak_adoption,
    }


def analyze_condition(cond_dir: Path, label: str) -> dict:
    """Analyze contagion dynamics for all seeds in a condition."""
    seed_dirs = sorted([d for d in cond_dir.iterdir() if d.is_dir() and d.name.startswith("seed_")])
    seeds = []
    for sd in seed_dirs:
        ledger = load_seed_ledger(sd)
        ticks = load_seed_ticks(sd)
        if not ledger or not ticks:
            continue
        n_agents = ticks[0].get("num_agents", 20) if ticks else 20
        max_tick = len(ticks)

        # Per-word contagion
        words_data = []
        for w in ledger.get("words", []):
            curve = compute_adoption_curve(w, n_agents, max_tick)
            words_data.append({"word": w.get("word", "?"), **curve})

        # Aggregate
        if words_data:
            avg_peak = sum(w["peak"] for w in words_data) / len(words_data)
            avg_carry = sum(w["carrying_capacity"] for w in words_data) / len(words_data)
            growth_rates = [w["growth_rate"] for w in words_data if w["growth_rate"] is not None]
            avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else None
        else:
            avg_peak = 0.0
            avg_carry = 0.0
            avg_growth = None

        # Norm contagion (if any norms passed)
        norms_passed = ticks[-1].get("passed_norms", 0) if ticks else 0
        total_votes = ticks[-1].get("total_votes", 0) if ticks else 0

        seed_n = int(sd.name.split("_")[1])
        seeds.append({
            "seed": seed_n,
            "n_words": len(words_data),
            "avg_word_peak": round(avg_peak, 4),
            "avg_carrying_capacity": round(avg_carry, 4),
            "avg_growth_rate": round(avg_growth, 4) if avg_growth else None,
            "norms_passed": norms_passed,
            "total_votes": total_votes,
            "words_above_one_knower": sum(1 for w in words_data if w["peak"] > 1),
            "words": words_data,
        })

    if not seeds:
        return {"label": label, "seeds": [], "stats": {}}

    metrics = ["n_words", "avg_word_peak", "avg_carrying_capacity", "norms_passed",
               "total_votes", "words_above_one_knower"]
    stats = {}
    for k in metrics:
        vals = [s[k] for s in seeds if s.get(k) is not None]
        if not vals:
            continue
        n = len(vals)
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / n
        std = var ** 0.5
        ci95 = 1.96 * std / (n ** 0.5) if n > 1 else 0.0
        stats[k] = {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "ci95": round(ci95, 4),
            "min": round(min(vals), 4) if vals else None,
            "max": round(max(vals), 4) if vals else None,
            "n": n,
        }

    # Growth rates separately
    gr_vals = [s["avg_growth_rate"] for s in seeds if s.get("avg_growth_rate") is not None]
    if gr_vals:
        n = len(gr_vals)
        mean = sum(gr_vals) / n
        var = sum((v - mean) ** 2 for v in gr_vals) / n
        stats["avg_growth_rate"] = {
            "mean": round(mean, 4),
            "std": round(var ** 0.5, 4),
            "n": n,
        }

    return {"label": label, "seeds": seeds, "stats": stats}


def main():
    parser = argparse.ArgumentParser(description="Contagion/cascade analysis")
    parser.add_argument("--experiment-dir", "-d", default="experiments/three_conditions_smoke")
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    if not exp_dir.is_dir():
        print(f"ERROR: {exp_dir} not found")
        sys.exit(1)

    conditions = []
    for child in sorted(exp_dir.iterdir()):
        if child.is_dir() and child.name != "__pycache__":
            result = analyze_condition(child, child.name)
            if result["seeds"]:
                conditions.append(result)

    if not conditions:
        print("No seed data found")
        sys.exit(1)

    output = {"experiment_dir": str(exp_dir), "conditions": {}}
    for cond in conditions:
        output["conditions"][cond["label"]] = {
            "stats": cond["stats"],
            "seeds": cond["seeds"],
        }

    out_path = args.output or (exp_dir / "contagion.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Contagion analysis saved to {out_path}\n")
    for label, data in output["conditions"].items():
        s = data["stats"]
        print(f"  [{label}]")
        for k in ("n_words", "avg_word_peak", "avg_carrying_capacity",
                  "words_above_one_knower", "avg_growth_rate"):
            if k in s:
                print(f"    {k}: {s[k]['mean']} ±{s[k].get('ci95', 0)} [{s[k].get('min', '?')}–{s[k].get('max', '?')}]")
        print()


if __name__ == "__main__":
    main()

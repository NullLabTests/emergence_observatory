#!/usr/bin/env python3
"""Semantic drift tracking for invented vocabulary.

Records per-tick snapshots of word meanings per agent, then computes:
  - Meaning consensus: fraction of meaning-knowers sharing the dominant meaning
  - Drift magnitude: semantic similarity between original and current meanings
  - Meaning diversity: distinct meanings per word across the population
  - Propagation depth: how many hops from inventor a meaning has travelled

Usage:
    python experiments/semantic_drift.py --experiment-dir experiments/three_conditions_smoke
"""

from __future__ import annotations
import sys, json, math, argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# N-gram similarity (fast, no LLM calls)
# ---------------------------------------------------------------------------

def _ngrams(s: str, n: int = 3) -> set[str]:
    """Character n-grams for a string."""
    s = s.lower().strip()
    return {s[i:i+n] for i in range(len(s) - n + 1)}


def meaning_similarity(a: str, b: str) -> float:
    """Jaccard similarity of character trigrams between two meaning strings."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ga = _ngrams(a)
    gb = _ngrams(b)
    if not ga and not gb:
        return 1.0
    intersect = len(ga & gb)
    union = len(ga | gb)
    return intersect / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# DriftRecorder — snapshots word meanings per tick during experiment runs
# ---------------------------------------------------------------------------

class DriftRecorder:
    """Records per-agent word meaning snapshots each tick for drift analysis.

    Usage in runner:
        drift = DriftRecorder()
        for t in range(ticks):
            sim.step()
            drift.observe(t, sim.agents.values())
        drift.save(seed_dir / "drift_snapshots.json")
    """

    def __init__(self):
        self.snapshots: list[dict] = []

    def observe(self, tick: int, agents: list) -> None:
        snap: dict[str, dict[str, str]] = {}
        for a in agents:
            if a.invented_words:
                snap[str(a.agent_id)] = dict(a.invented_words)
        self.snapshots.append({"tick": tick, "agents": snap})

    def save(self, path: str | Path) -> None:
        with open(path, "w") as f:
            json.dump(self.snapshots, f, indent=1)

    @classmethod
    def load(cls, path: str | Path) -> list[dict]:
        with open(path) as f:
            return json.load(f)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_seed_snapshots(snapshots: list[dict]) -> dict:
    """Analyze semantic drift from per-tick meaning snapshots for one seed.

    Returns dict with per-word lifecycle and aggregate drift metrics.
    """
    # Build per-word timeline: {word: [(tick, {agent_id: meaning}), ...]}
    word_timeline: dict[str, list[tuple[int, dict[str, str]]]] = {}
    inventor: dict[str, tuple[int, str, str]] = {}  # word -> (agent_id, tick, meaning)
    all_agent_ids: set[str] = set()

    for entry in snapshots:
        tick = entry["tick"]
        agents_data = entry.get("agents", {})
        all_agent_ids.update(agents_data.keys())

        # Collect meanings per word at this tick
        tick_meanings: dict[str, dict[str, str]] = defaultdict(dict)
        for aid, words in agents_data.items():
            for word, meaning in words.items():
                tick_meanings[word][aid] = meaning

        for word, agent_meanings in tick_meanings.items():
            if word not in word_timeline:
                word_timeline[word] = []
            word_timeline[word].append((tick, dict(agent_meanings)))

            # Record inventor (first seen)
            if word not in inventor:
                for aid, meaning in agent_meanings.items():
                    inventor[word] = (aid, tick, meaning)
                    break

    if not word_timeline:
        return {}

    # Per-word analysis
    per_word = {}
    all_drift_magnitudes = []
    all_consensus_scores = []

    for word, timeline in word_timeline.items():
        inv_info = inventor.get(word, (None, None, None))
        inv_agent, inv_tick, inv_meaning = inv_info

        # Track meaning diversity at each tick
        ticks = []
        distinct_meanings = []
        dominant_fractions = []
        drift_mags = []

        for tick, agent_meanings in timeline:
            ticks.append(tick)
            # Count unique meanings
            meanings_list = list(agent_meanings.values())
            unique = len(set(meanings_list))
            distinct_meanings.append(unique)

            # Dominant meaning fraction
            if meanings_list:
                counts = defaultdict(int)
                for m in meanings_list:
                    counts[m] += 1
                most_common_count = max(counts.values())
                dominant_fractions.append(most_common_count / len(meanings_list))

                # Drift magnitude: similarity to inventor meaning
                if inv_meaning:
                    sims = [meaning_similarity(m, inv_meaning) for m in meanings_list]
                    drift_mags.append(1.0 - (sum(sims) / len(sims)))
                else:
                    drift_mags.append(0.0)
            else:
                distinct_meanings.append(0)
                dominant_fractions.append(1.0)
                drift_mags.append(0.0)

        final_drift = drift_mags[-1] if drift_mags else 0.0
        final_consensus = dominant_fractions[-1] if dominant_fractions else 1.0

        per_word[word] = {
            "word": word,
            "inventor_agent": inv_agent,
            "inventor_tick": inv_tick,
            "inventor_meaning": inv_meaning,
            "max_meaning_diversity": max(distinct_meanings) if distinct_meanings else 0,
            "final_meaning_diversity": distinct_meanings[-1] if distinct_meanings else 0,
            "final_consensus": round(final_consensus, 4),
            "final_drift_magnitude": round(final_drift, 4),
            "peak_known_by": max(len(am) for _, am in timeline) if timeline else 0,
            "meanings_over_time": [{"tick": t, "n_meanings": d, "consensus": round(cf, 4), "drift": round(dm, 4)}
                                    for t, d, cf, dm in zip(ticks, distinct_meanings, dominant_fractions, drift_mags)],
        }
        all_drift_magnitudes.append(final_drift)
        all_consensus_scores.append(final_consensus)

    # Aggregate
    n_words = len(per_word)
    drift_mean = sum(all_drift_magnitudes) / n_words if n_words else 0.0
    consensus_mean = sum(all_consensus_scores) / n_words if n_words else 1.0
    total_knowers = sum(w["peak_known_by"] for w in per_word.values())
    mean_knowers = total_knowers / n_words if n_words else 0.0

    return {
        "n_words": n_words,
        "mean_drift_magnitude": round(drift_mean, 4),
        "mean_consensus": round(consensus_mean, 4),
        "mean_peak_knowers": round(mean_knowers, 2),
        "words": per_word,
    }


def analyze_condition(cond_dir: Path, label: str) -> dict:
    """Analyze semantic drift across all seeds in one condition."""
    seed_dirs = sorted([d for d in cond_dir.iterdir() if d.is_dir() and d.name.startswith("seed_")])
    seeds = []
    for sd in seed_dirs:
        snap_path = sd / "drift_snapshots.json"
        if not snap_path.exists():
            continue
        snapshots = DriftRecorder.load(snap_path)
        result = analyze_seed_snapshots(snapshots)
        if result:
            seed_n = int(sd.name.split("_")[1])
            result["seed"] = seed_n
            seeds.append(result)

    if not seeds:
        return {"label": label, "seeds": [], "stats": {}}

    metrics = ["n_words", "mean_drift_magnitude", "mean_consensus", "mean_peak_knowers"]
    stats = {}
    for k in metrics:
        vals = [s[k] for s in seeds if k in s]
        if not vals:
            continue
        n = len(vals)
        mean = sum(vals) / n
        variance = sum((v - mean) ** 2 for v in vals) / n
        std = variance ** 0.5
        ci95 = 1.96 * std / (n ** 0.5) if n > 1 else 0.0
        stats[k] = {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "ci95": round(ci95, 4),
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "n": n,
        }

    return {"label": label, "seeds": seeds, "stats": stats}


def main():
    parser = argparse.ArgumentParser(description="Semantic drift analysis")
    parser.add_argument("--experiment-dir", "-d", default="experiments/three_conditions_smoke",
                        help="Path to experiment directory")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON path")
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
        print("No drift snapshots found. Run an experiment with DriftRecorder enabled first.")
        sys.exit(1)

    output = {"experiment_dir": str(exp_dir), "conditions": {}}
    for cond in conditions:
        output["conditions"][cond["label"]] = {
            "stats": cond["stats"],
            "seeds": cond["seeds"],
        }

    out_path = args.output or (exp_dir / "semantic_drift.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Semantic drift analysis saved to {out_path}\n")
    for label, data in output["conditions"].items():
        s = data["stats"]
        print(f"  [{label}]")
        for k in ("n_words", "mean_drift_magnitude", "mean_consensus", "mean_peak_knowers"):
            if k in s:
                print(f"    {k}: {s[k]['mean']} ±{s[k]['ci95']} [{s[k]['min']}–{s[k]['max']}]")
        print()


if __name__ == "__main__":
    main()

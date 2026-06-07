#!/usr/bin/env python3
"""Generate publication-ready LaTeX tables and summaries from experiment data.

Usage:
    python papers/generate_report.py --experiment-dir experiments/three_conditions
"""

from __future__ import annotations
import sys, json, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def fmt_val(v, decimals: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{decimals}f}"
    return str(v)


def make_comparison_table(comparison: dict) -> str:
    """Generate LaTeX table comparing conditions."""
    labels = [k for k in comparison if k != "between_condition_tests"]
    if len(labels) < 2:
        return ""

    metric_labels = {
        "vocab_size": "Final vocab size",
        "total_words_invented": "Words invented",
        "mean_word_lifetime": "Mean word lifetime (ticks)",
        "passed_norms": "Norms passed",
        "total_votes": "Votes cast",
        "num_alliances": "Alliances formed",
        "num_groups": "Groups formed",
        "total_research": "Research findings",
        "llm_calls": "LLM calls",
        "llm_failures": "LLM failures",
        "max_word_lifetime": "Max word lifetime (ticks)",
        "alive_words": "Words still alive",
        "extinct_words": "Extinct words",
        "zipf_alpha": "Zipf $\\alpha$",
        "heaps_beta": "Heaps $\\beta$",
        "mean_drift_magnitude": "Drift magnitude",
        "mean_consensus": "Meaning consensus",
    }

    header_metrics = [
        "vocab_size", "total_words_invented", "mean_word_lifetime",
        "passed_norms", "total_votes", "num_alliances", "num_groups",
    ]

    lines = [
        "\\begin{table}[ht]",
        "\\centering",
        "\\begin{tabular}{l" + "c" * len(labels) + "}",
        "\\toprule",
        "Metric & " + " & ".join(f"\\textbf{{{l.replace('_', ' ')}}}" for l in labels) + " \\\\",
        "\\midrule",
    ]

    for metric in header_metrics:
        row_vals = []
        for label in labels:
            s = comparison.get(label, {}).get("stats", {}).get(metric, {})
            if s:
                mean = s.get("mean", 0)
                ci = s.get("ci95", 0)
                row_vals.append(f"${fmt_val(mean)} \\pm {fmt_val(ci)}$")
            else:
                row_vals.append("—")
        name = metric_labels.get(metric, metric.replace("_", " "))
        lines.append(f"{name} & " + " & ".join(row_vals) + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append(f"\\caption{{Comparison across {', '.join(labels)} conditions. "
                 f"Values are mean $\\pm$ 95\\% CI.}}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def make_mwt_table(comparison: dict) -> str:
    """Generate LaTeX table for Mann-Whitney U tests."""
    tests = comparison.get("between_condition_tests", {})
    if not tests:
        return ""

    metric_labels = {
        "vocab_size": "Vocabulary size",
        "total_words_invented": "Words invented",
        "mean_word_lifetime": "Word lifetime",
        "passed_norms": "Norms passed",
        "total_votes": "Votes cast",
        "num_alliances": "Alliances",
        "num_groups": "Groups",
        "total_research": "Research findings",
        "zipf_alpha": "Zipf $\\alpha$",
        "heaps_beta": "Heaps $\\beta$",
        "max_peak_adoption": "Peak adoption",
    }

    lines = [
        "\\begin{table}[ht]",
        "\\centering",
        "\\begin{tabular}{lcc}",
        "\\toprule",
        "Comparison & Metric & $p$-value \\\\",
        "\\midrule",
    ]

    for key, metrics in tests.items():
        first = True
        for metric, res in metrics.items():
            p = res.get("p_value")
            if p is None:
                continue
            p_str = f"${p:.4f}$"
            if p < 0.001:
                p_str += "$^{***}$"
            elif p < 0.01:
                p_str += "$^{**}$"
            elif p < 0.05:
                p_str += "$^{*}$"
            comp_str = key.replace("_vs_", " vs ") if first else ""
            lines.append(f"{comp_str} & {metric_labels.get(metric, metric)} & {p_str} \\\\")
            first = False

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\caption{Mann-Whitney U tests between conditions. "
                 "$^{*}p<0.05$, $^{**}p<0.01$, $^{***}p<0.001$.}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def make_drift_table(drift_data: dict) -> str:
    """Generate LaTeX table for semantic drift metrics."""
    conditions = drift_data.get("conditions", {})
    if not conditions:
        return ""

    lines = [
        "\\begin{table}[ht]",
        "\\centering",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Condition & Words & Drift magnitude & Meaning consensus \\\\",
        "\\midrule",
    ]

    for label, data in conditions.items():
        s = data.get("stats", {})
        nw = s.get("n_words", {})
        dm = s.get("mean_drift_magnitude", {})
        mc = s.get("mean_consensus", {})
        lines.append(
            f"{label.replace('_', ' ')} & "
            f"${fmt_val(nw.get('mean', 0), 1)} \\pm {fmt_val(nw.get('ci95', 0), 1)}$ & "
            f"${fmt_val(dm.get('mean', 0), 3)} \\pm {fmt_val(dm.get('ci95', 0), 3)}$ & "
            f"${fmt_val(mc.get('mean', 0), 3)} \\pm {fmt_val(mc.get('ci95', 0), 3)}$ \\\\"
        )

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\caption{Semantic drift metrics across conditions. "
                 "Drift magnitude is 1 $-$ trigram Jaccard similarity to inventor meaning. "
                 "Consensus is fraction of knowers sharing the dominant meaning.}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def make_contagion_table(contagion_data: dict) -> str:
    """Generate LaTeX table for contagion metrics."""
    conditions = contagion_data.get("conditions", {})
    if not conditions:
        return ""

    lines = [
        "\\begin{table}[ht]",
        "\\centering",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Condition & Words & Peak adoption & Growth rate \\\\",
        "\\midrule",
    ]

    for label, data in conditions.items():
        s = data.get("stats", {})
        nw = s.get("n_words", {})
        ap = s.get("avg_word_peak", {})
        gr = s.get("avg_growth_rate", {})
        gr_str = f"${fmt_val(gr.get('mean', 0), 4)}$" if gr else "—"
        lines.append(
            f"{label.replace('_', ' ')} & "
            f"${fmt_val(nw.get('mean', 0), 1)} \\pm {fmt_val(nw.get('ci95', 0), 1)}$ & "
            f"${fmt_val(ap.get('mean', 0), 2)} \\pm {fmt_val(ap.get('ci95', 0), 2)}$ & "
            f"{gr_str} \\\\"
        )

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\caption{Contagion metrics across conditions. "
                 "Peak adoption is the maximum number of agents simultaneously using a word. "
                 "Growth rate is the logistic slope parameter.}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate LaTeX report from experiment data")
    parser.add_argument("--experiment-dir", "-d", required=True)
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    exp_dir = Path(args.experiment_dir)
    if not exp_dir.is_dir():
        print(f"ERROR: {exp_dir} not found")
        sys.exit(1)

    # Load data
    comparison = {}
    comp_path = exp_dir / "comparison.json"
    if comp_path.exists():
        comparison = load_json(comp_path)
        print(f"  Loaded comparison.json ({len(comparison)} conditions)")

    drift_data = {}
    drift_path = exp_dir / "semantic_drift.json"
    if drift_path.exists():
        drift_data = load_json(drift_path)
        print(f"  Loaded semantic_drift.json")

    contagion_data = {}
    contagion_path = exp_dir / "contagion.json"
    if contagion_path.exists():
        contagion_data = load_json(contagion_path)
        print(f"  Loaded contagion.json")

    if not comparison and not drift_data and not contagion_data:
        print("ERROR: no experiment data found")
        sys.exit(1)

    out_path = Path(args.output) if args.output else exp_dir / "report.tex"
    sections = []

    if comparison:
        sections.append("% Comparison table")
        sections.append(make_comparison_table(comparison))
        sections.append("")
        sections.append("% Mann-Whitney U tests")
        sections.append(make_mwt_table(comparison))
        sections.append("")

    if drift_data:
        sections.append("% Semantic drift table")
        sections.append(make_drift_table(drift_data))
        sections.append("")

    if contagion_data:
        sections.append("% Contagion table")
        sections.append(make_contagion_table(contagion_data))
        sections.append("")

    preamble = """% Auto-generated by papers/generate_report.py
% Compile with: pdflatex report.tex
\\documentclass{article}
\\usepackage{booktabs}
\\usepackage[margin=1in]{geometry}
\\begin{document}
\\title{Emergence Observatory Experiment Report}
\\maketitle
"""

    footer = "\\end{document}"

    with open(out_path, "w") as f:
        f.write(preamble)
        f.write("\n".join(sections))
        f.write(footer)

    print(f"\n  Report saved to {out_path}")
    print(f"  Compile with: pdflatex {out_path}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render activation eval summaries as charts.

This module owns all Matplotlib code. It imports Matplotlib directly because the
project declares it as a dependency (see ``pyproject.toml``); metric computation
stays in ``scripts.evals.summarize_evals`` and never imports a plotting library.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from scripts.evals.summarize_evals import load_entries

SPLIT_STYLES = {
    "train": {"color": "tab:blue", "linestyle": "-", "marker": "o"},
    "validation": {"color": "tab:orange", "linestyle": "--", "marker": "s"},
    "smoke": {"color": "tab:green", "linestyle": ":", "marker": "^"},
}
TREND_METRICS = ("precision", "recall", "f1", "accuracy")

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [
        "DejaVu Sans",
        "Noto Sans CJK SC",
        "Microsoft YaHei",
        "SimHei",
    ],
    "axes.unicode_minus": False,
})


def confusion_matrix(summary: dict, output: Path) -> None:
    """Render the routing confusion matrix to a PNG file.

    中文：绘制正负样本、读取状态和不可判定列，并把图像写入 output。
    """
    overall = summary["overall"]
    matrix = [
        [overall["tp"], overall["fn"], overall["inconclusive_positive"]],
        [overall["fp"], overall["tn"], overall["inconclusive_negative"]],
    ]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    image = ax.imshow(matrix, cmap="Blues", aspect="auto")
    ax.set_xticks(range(3), ["loaded", "not loaded", "inconclusive"])
    ax.set_yticks(range(2), ["positive", "negative"])
    ax.set_xlabel("predicted")
    ax.set_ylabel("actual")
    ax.set_title("Routing confusion matrix")
    fig.colorbar(image, ax=ax, fraction=0.046)
    maximum = max(max(row) for row in matrix)
    for row in range(2):
        for col in range(3):
            value = matrix[row][col]
            ax.text(
                col,
                row,
                str(value),
                ha="center",
                va="center",
                color="white" if value > maximum / 2 else "black",
            )
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def per_skill_bars(summary: dict, output: Path) -> None:
    """Render per-skill precision and recall bars.

    中文：按 skill 绘制 precision/recall 对比柱状图并保存 PNG。
    """
    skills = list(summary["per_skill"])
    precision = [summary["per_skill"][s]["precision"] or 0.0 for s in skills]
    recall = [summary["per_skill"][s]["recall"] or 0.0 for s in skills]
    x = list(range(len(skills)))
    width = 0.38
    fig, ax = plt.subplots(figsize=(max(7, len(skills) * 0.8), 4))
    ax.bar([i - width / 2 for i in x], precision, width, label="precision")
    ax.bar([i + width / 2 for i in x], recall, width, label="recall")
    ax.set_xticks(x, skills, rotation=45, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("rate")
    ax.set_title("Precision and recall per skill")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def per_skill_errors(summary: dict, output: Path) -> None:
    """Show missed activations and false activations by skill and sample size.

    Undefined rates are labeled N/A instead of being drawn as zero; an
    infrastructure failure never enters an error-rate denominator.
    中文：按 skill 绘制 FNR/FPR 与有效样本数；分母为零时显示 N/A，而非伪造零误差。
    """
    per_skill = summary["per_skill"]
    skills = sorted(per_skill, key=lambda name: per_skill[name]["false_negative_rate"] or 0, reverse=True)
    fig, ax = plt.subplots(figsize=(10, max(4, len(skills) * 0.55 + 1.4)))
    for index, skill in enumerate(skills):
        values = per_skill[skill]
        for offset, key, color in (
            (-0.18, "false_negative_rate", "tab:orange"),
            (0.18, "false_positive_rate", "tab:blue"),
        ):
            rate = values[key]
            if rate is None:
                ax.text(0.01, index + offset, "N/A", va="center", fontsize=8)
            else:
                ax.barh(index + offset, rate, height=0.32, color=color)
    labels = [
        f"{skill}  (pos={per_skill[skill]['tp'] + per_skill[skill]['fn']}, "
        f"neg={per_skill[skill]['tn'] + per_skill[skill]['fp']}, "
        f"inc={per_skill[skill]['inconclusive']})"
        for skill in skills
    ]
    ax.set_yticks(range(len(skills)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Error rate on decided trials")
    ax.set_title("Missed and false skill activations")
    ax.legend(handles=[
        Patch(color="tab:orange", label="FNR (missed positives)"),
        Patch(color="tab:blue", label="FPR (false activations)"),
    ], loc="lower right")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def radar_chart(summary: dict, output: Path, label: str = "") -> bool:
    """Render per-skill precision, recall, and F1 radar charts.

    Each radar uses the skills as spokes and one metric as its polygon, so a
    skill whose precision collapses is visible as a dent in that spoke.
    中文：以 skill 为轴绘制三张雷达图；少于三个 skill 时跳过并返回 False。
    """
    per_skill = summary.get("per_skill") or {}
    skills = list(per_skill)
    if len(skills) < 3:
        print(f"radar chart skipped: need at least 3 skills, got {len(skills)}")
        return False

    metrics = ("precision", "recall", "f1")
    titles = {"precision": "precision", "recall": "recall", "f1": "F1"}
    angles = [index * 2 * math.pi / len(skills) for index in range(len(skills))]
    angles_closed = angles + angles[:1]

    fig, axes = plt.subplots(1, 3, subplot_kw={"polar": True}, figsize=(18, 6.2))
    for ax, metric in zip(axes, metrics):
        values = [per_skill[skill].get(metric) or 0.0 for skill in skills]
        values_closed = values + values[:1]
        ax.plot(angles_closed, values_closed, color="#4c72b0", linewidth=1.5)
        ax.fill(angles_closed, values_closed, color="#4c72b0", alpha=0.2)
        ax.set_xticks(angles)
        ax.set_xticklabels(skills, fontsize=8)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["0.25", "0.5", "0.75", "1.0"], fontsize=6)
        ax.set_title(f"{titles[metric]}{(' ' + label) if label else ''}", fontsize=11)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return True


def inconclusive_bars(summary: dict, output: Path) -> None:
    """Render infrastructure-inconclusive counts by reason.

    中文：按规范化失败原因绘制不可判定 trial 横向柱状图并保存 PNG。
    """
    reasons = summary["inconclusive_reasons"]
    labels = sorted(reasons)
    fig, ax = plt.subplots(figsize=(6, max(2.6, len(labels) * 0.5 + 1.2)))
    if labels:
        values = [reasons[label] for label in labels]
        ax.barh(labels[::-1], values[::-1], color="#4c72b0")
    else:
        ax.barh(["none"], [0], color="#4c72b0")
    ax.set_xlabel("trials")
    ax.set_title("Inconclusive trials by infrastructure reason")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def trigger_rate_distribution(summary: dict, output: Path) -> None:
    """Render repeated-query activation rates without treating them as scores.

    中文：分别绘制正负 query 的触发率分布；该分布只表示稳定性，不是校准分数。
    """
    positive = []
    negative = []
    for query in summary.get("per_query", []):
        rate = query.get("trigger_rate")
        if rate is None:
            continue
        (positive if query.get("should_trigger") else negative).append(rate)

    fig, ax = plt.subplots(figsize=(7, 4))
    bins = [index / 10 for index in range(11)]
    ax.hist(
        [positive, negative],
        bins=bins,
        label=["should trigger", "should not trigger"],
        color=["tab:blue", "tab:orange"],
        alpha=0.75,
    )
    ax.set_xlim(0, 1)
    ax.set_xlabel("observed trigger rate per query")
    ax.set_ylabel("queries")
    ax.set_title("Repeated-query routing stability")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def iteration_trend(entries: list[dict], output: Path) -> None:
    """Compare one split pair or render trends over repeated snapshots.

    中文：只有 train/validation 各一次时绘制对比柱图；有多轮快照时再绘制迭代折线。
    """
    groups: dict[str, list[dict]] = {}
    for entry in entries:
        groups.setdefault(entry["split"], []).append(entry["summary"]["overall"])

    titles = {"precision": "precision", "recall": "recall", "f1": "F1", "accuracy": "accuracy"}
    fig, axes = plt.subplots(1, len(TREND_METRICS), figsize=(5 * len(TREND_METRICS), 4))
    single_snapshot = all(len(values) == 1 for values in groups.values())
    for ax, key in zip(axes, TREND_METRICS):
        for split, values in sorted(groups.items()):
            style = SPLIT_STYLES.get(split, {"color": "tab:gray", "linestyle": "-", "marker": "x"})
            series = [item[key] for item in values]
            if single_snapshot:
                if series[0] is not None:
                    ax.bar(split, series[0], color=style["color"])
                else:
                    ax.text(split, 0.02, "N/A", ha="center")
                continue
            iterations = list(range(1, len(values) + 1))
            ax.plot(
                iterations,
                series,
                marker=style["marker"],
                linestyle=style["linestyle"],
                color=style["color"],
                label=split,
            )
        ax.set_title(titles[key])
        ax.set_ylabel("rate")
        ax.set_ylim(0, 1.05)
        if not single_snapshot:
            ax.set_xlabel("iteration")
            ax.set_xticks(list(range(1, max(len(values) for values in groups.values()) + 1)))
            ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main() -> int:
    """Render the supported chart set from activation result files.

    中文：解析结果文件、标签和输出目录，生成 README 与分析使用的 PNG 图表。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="activation result JSON files")
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results"))
    parser.add_argument("--prefix", default="routing", help="chart filename prefix")
    parser.add_argument(
        "--exclude-id", action="append", default=[],
        help="omit one historical case ID from chart counts (repeatable)",
    )
    parser.add_argument(
        "--label",
        action="append",
        help="split label for each file, in order; defaults to filename inference",
    )
    args = parser.parse_args()
    if args.label and len(args.label) > len(args.files):
        parser.error("more --label values than files")

    entries = load_entries(args.files, args.label or [], set(args.exclude_id))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    first = entries[0]
    confusion_matrix(first["summary"], args.output_dir / f"{args.prefix}-confusion.png")
    per_skill_bars(first["summary"], args.output_dir / f"{args.prefix}-per-skill.png")
    per_skill_errors(first["summary"], args.output_dir / f"{args.prefix}-per-skill-errors.png")
    radar_chart(
        first["summary"],
        args.output_dir / f"{args.prefix}-radar.png",
        label=first["split"],
    )
    inconclusive_bars(first["summary"], args.output_dir / f"{args.prefix}-inconclusive.png")
    trigger_rate_distribution(
        first["summary"], args.output_dir / f"{args.prefix}-trigger-rate.png"
    )
    if len(entries) > 1:
        iteration_trend(entries, args.output_dir / f"{args.prefix}-trend.png")
    print(f"wrote charts to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

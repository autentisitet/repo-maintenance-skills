#!/usr/bin/env python3
"""Derive routing metrics from activation results (standard library only).

Semantics
---------
* The runner reports ``pass``, ``fail``, and ``inconclusive`` per trial.
* ``inconclusive`` with an ``infrastructure_failure`` marker means the run gave
  no reliable evidence (timeout, process failure, missing completion event, or
  an unavailable evaluation). These trials are counted separately and never
  enter a precision/recall/FPR/FNR/specificity/F1/accuracy denominator.
* Harness v6 records every reliable routing mismatch as ``fail``. For backward
  compatibility, a legacy ``inconclusive`` without an infrastructure marker is
  interpreted as a completed positive miss (false negative).

The report intentionally omits ROC/AUC/P-R curves: trials carry a discrete
pass/fail/inconclusive decision rather than a continuous score, so plotting a
continuous curve would fabricate data. Rendering the supported charts lives in
``scripts.evals.plot_evals``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from scripts.evals.run_activation_evals import runner_digest

ROOT = Path(__file__).resolve().parents[2]

# Canonical infrastructure-failure labels. The harness uses the longer reason
# strings on the left; the short labels on the right are shown in reports.
REASON_LABELS = {
    "timeout": "timeout",
    "agent_process_failed": "process_failed",
    "completion_event_missing": "completion_missing",
    "evaluation_unavailable": "unavailable",
}


def classify(trial: dict, should_trigger: bool) -> str:
    """Map one trial to a confusion or infrastructure bucket.

    ``pass`` means the observed read matched the expectation, ``fail`` means it
    did not. Current ``inconclusive`` rows are infrastructure failures with no
    reliable evidence. Legacy non-infrastructure inconclusive rows are treated
    as routing false negatives rather than missing evidence.
    中文：根据标签、status 和基础设施标记，把 trial 归入 TP/FN/FP/TN 或不可判定桶。
    """
    status = trial.get("status")
    if status == "pass":
        return "tp" if should_trigger else "tn"
    if status == "fail":
        return "fp" if not should_trigger else "fn"
    if trial.get("infrastructure_failure"):
        return "inc_pos" if should_trigger else "inc_neg"
    return "fn" if should_trigger else "inc_neg"


def ratio(numerator: int, denominator: int) -> float | None:
    """Return a rounded ratio or None for an empty denominator.

    中文：计算四位小数比率；分母为零时返回 None，避免伪造数值。
    """
    return round(numerator / denominator, 4) if denominator else None


def percentile(ordered: list[float], quantile: float) -> float | None:
    """Return a linearly interpolated quantile from sorted values.

    Design/System considerations: The function uses the ``q * (n - 1)`` linear interpolation
    convention, so P95 remains defined for small samples without pretending an observed element is
    the exact percentile.
    中文：对已排序数值做线性插值；空输入返回 None。

    设计/系统考虑：采用 ``q * (n - 1)`` 线性插值，使小样本也能定义 P95，同时不把某个观测值伪装
    成精确分位点。
    """
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    position = quantile * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def duration_stats(values: list[float]) -> dict:
    """Summarize wall-clock durations for independent trial sessions.

    中文：计算 trial 墙钟时间的数量、总和、均值、中位数、P95、最小值和最大值。
    """
    if not values:
        return {
            "count": 0,
            "total": None,
            "mean": None,
            "median": None,
            "p95": None,
            "min": None,
            "max": None,
        }
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    median = ordered[midpoint]
    if len(ordered) % 2 == 0:
        median = (ordered[midpoint - 1] + ordered[midpoint]) / 2
    return {
        "count": len(values),
        "total": round(sum(values), 2),
        "mean": round(sum(values) / len(values), 2),
        "median": round(median, 2),
        "p95": round(percentile(ordered, 0.95) or 0.0, 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
    }


def metrics(tp: int, fn: int, fp: int, tn: int) -> dict:
    """Compute routing rates from decided confusion counts.

    Design/System considerations: Infrastructure-inconclusive trials are excluded from every
    routing denominator. Undefined ratios remain ``None`` instead of being coerced to zero, while
    F1 is zero only when both defined precision and recall are zero.
    中文：由 TP/FN/FP/TN 计算 precision、recall、specificity、F1 和准确率；不含不可判定 trial。

    设计/系统考虑：基础设施不可判定不进入任何路由分母；无定义比率保留为 ``None``，只有 precision
    与 recall 均已定义且为零时 F1 才记为零。
    """
    decided = tp + fn + fp + tn
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    if precision is not None and recall is not None:
        f1 = 0.0 if precision + recall == 0 else round(
            2 * precision * recall / (precision + recall), 4
        )
    else:
        f1 = None
    specificity = ratio(tn, tn + fp)
    balanced_accuracy = (
        round((recall + specificity) / 2, 4)
        if recall is not None and specificity is not None
        else None
    )
    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "decided": decided,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": ratio(fp, fp + tn),
        "false_negative_rate": ratio(fn, fn + tp),
        "specificity": specificity,
        "accuracy": ratio(tp + tn, decided),
        "balanced_accuracy": balanced_accuracy,
    }


def trial_loaded(trial: dict, should_trigger: bool) -> bool | None:
    """Return observed activation or None when evidence is unavailable.

    Design/System considerations: Explicit ``observed_skill_read`` wins over inferred status.
    Legacy status inference exists only for backward compatibility and never converts an
    infrastructure failure into routing evidence.
    中文：优先读取显式 evidence，并兼容旧结果 status；基础设施失败返回 None。

    设计/系统考虑：显式 ``observed_skill_read`` 优先于 status 推断；旧格式兼容逻辑绝不会把基础设施
    失败转换为路由证据。
    """
    if trial.get("infrastructure_failure"):
        return None
    observed = trial.get("observed_skill_read")
    if isinstance(observed, bool):
        return observed
    if trial.get("status") == "pass":
        return should_trigger
    if trial.get("status") == "fail":
        return not should_trigger
    return False


def query_metrics(row: dict) -> dict:
    """Summarize repeated clean-context trials for one query.

    中文：统计单条 query 的有效 trial、读取次数、触发率、期望结果率和稳定性。
    """
    should = bool(row.get("should_trigger"))
    loaded = 0
    valid = 0
    inconclusive = 0
    for trial in row.get("trials", []):
        activation = trial_loaded(trial, should)
        if activation is None:
            inconclusive += 1
            continue
        valid += 1
        loaded += int(activation)
    trigger_rate = ratio(loaded, valid)
    expected_rate = trigger_rate if should else (
        round(1 - trigger_rate, 4) if trigger_rate is not None else None
    )
    return {
        "id": str(row.get("id") or "unknown"),
        "skill": str(row.get("skill") or "unknown"),
        "category": str(row.get("category") or "unknown"),
        "should_trigger": should,
        "loaded_trials": loaded,
        "valid_trials": valid,
        "inconclusive_trials": inconclusive,
        "trigger_rate": trigger_rate,
        "expected_outcome_rate": expected_rate,
        "stable": valid >= 2 and loaded in {0, valid},
    }


def normalize_reason(reason: object) -> str:
    """Normalize raw infrastructure reasons to stable report labels.

    中文：把 runner 原始 reason 映射为稳定短标签，未知值统一归为 other。
    """
    if not isinstance(reason, str) or not reason:
        return "unavailable"
    return REASON_LABELS.get(reason, "other")


def inconclusive_reasons(result: dict) -> dict[str, int]:
    """Count infrastructure failures by canonical reason label.

    中文：遍历结果中的不可判定 trial，按规范化原因累计基础设施故障次数。
    """
    counts: dict[str, int] = {}
    for row in result.get("results", []):
        for trial in row.get("trials", []):
            if trial.get("status") == "inconclusive" and trial.get("infrastructure_failure"):
                label = normalize_reason(trial.get("reason"))
                counts[label] = counts.get(label, 0) + 1
    return counts


def compute_summary(result: dict) -> dict:
    """Aggregate a runner payload into routing, cost, and stability metrics.

    中文：生成整体、按 skill、按 category 和按 query 的指标，并汇总耗时与 token。
    """
    counts = {"tp": 0, "fn": 0, "fp": 0, "tn": 0, "inc_pos": 0, "inc_neg": 0}
    per_skill: dict[str, dict] = {}
    per_category: dict[str, dict] = {}
    passes = failures = 0
    durations: list[float] = []
    skill_durations: dict[str, list[float]] = {}
    usage_totals = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
    skill_usage: dict[str, dict[str, int]] = {}
    per_query = []

    for row in result.get("results", []):
        skill = str(row.get("skill") or "unknown")
        should = bool(row.get("should_trigger"))
        category = str(row.get("category") or "unknown")
        skill_counts = per_skill.setdefault(skill, dict.fromkeys(counts, 0))
        category_counts = per_category.setdefault(category, dict.fromkeys(counts, 0))
        per_query.append(query_metrics(row))
        for trial in row.get("trials", []):
            key = classify(trial, should)
            counts[key] += 1
            skill_counts[key] += 1
            category_counts[key] += 1
            status = trial.get("status")
            if status == "pass":
                passes += 1
            elif status == "fail":
                failures += 1
            duration = trial.get("duration_seconds")
            if type(duration) in (int, float):
                durations.append(float(duration))
                skill_durations.setdefault(skill, []).append(float(duration))
            usage = trial.get("usage")
            if isinstance(usage, dict):
                skill_totals = skill_usage.setdefault(
                    skill, {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
                )
                for key in usage_totals:
                    value = usage.get(key)
                    if type(value) is int:
                        usage_totals[key] += value
                        skill_totals[key] += value

    total = sum(counts.values())
    inconclusive_total = counts["inc_pos"] + counts["inc_neg"]
    overall = metrics(counts["tp"], counts["fn"], counts["fp"], counts["tn"])
    overall.update({
        "inconclusive_positive": counts["inc_pos"],
        "inconclusive_negative": counts["inc_neg"],
        "inconclusive_total": inconclusive_total,
        "total_trials": total,
        "decided_trials": counts["tp"] + counts["fn"] + counts["fp"] + counts["tn"],
        "coverage": (
            round((counts["tp"] + counts["fn"] + counts["fp"] + counts["tn"]) / total, 4)
            if total
            else None
        ),
        "inconclusive_rate": round(inconclusive_total / total, 4) if total else None,
        "inconclusive_positive_rate": ratio(counts["inc_pos"], counts["tp"] + counts["fn"] + counts["inc_pos"]),
        "inconclusive_negative_rate": ratio(counts["inc_neg"], counts["tn"] + counts["fp"] + counts["inc_neg"]),
        "passes": passes,
        "failures": failures,
        "pass_rate": round(passes / total, 4) if total else None,
        "duration_seconds": duration_stats(durations),
        "usage": {
            **usage_totals,
            "reported_total_tokens": usage_totals["input_tokens"] + usage_totals["output_tokens"],
        },
        "tokens_per_second": (
            round(usage_totals["output_tokens"] / sum(durations), 2)
            if durations and usage_totals["output_tokens"]
            else None
        ),
    })

    skill_summaries = {}
    for skill, values in sorted(per_skill.items()):
        entry = metrics(values["tp"], values["fn"], values["fp"], values["tn"])
        entry["inconclusive"] = values["inc_pos"] + values["inc_neg"]
        entry["inconclusive_rate"] = ratio(
            values["inc_pos"] + values["inc_neg"],
            sum(values[key] for key in ("tp", "fn", "fp", "tn", "inc_pos", "inc_neg")),
        )
        entry["mean_duration_seconds"] = (
            round(sum(skill_durations[skill]) / len(skill_durations[skill]), 2)
            if skill_durations.get(skill)
            else None
        )
        entry["median_duration_seconds"] = (
            round(duration_stats(skill_durations.get(skill, []))["median"] or 0.0, 2)
            if skill_durations.get(skill)
            else None
        )
        entry["p95_duration_seconds"] = (
            round(duration_stats(skill_durations.get(skill, []))["p95"] or 0.0, 2)
            if skill_durations.get(skill)
            else None
        )
        entry["usage"] = dict(skill_usage.get(skill, {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}))
        entry["usage"]["reported_total_tokens"] = (
            entry["usage"]["input_tokens"] + entry["usage"]["output_tokens"]
        )
        entry["tokens_per_second"] = (
            round(entry["usage"]["output_tokens"] / sum(skill_durations[skill]), 2)
            if skill_durations.get(skill) and entry["usage"]["output_tokens"]
            else None
        )
        entry["trials"] = sum(
            values[key] for key in ("tp", "fn", "fp", "tn", "inc_pos", "inc_neg")
        )
        skill_summaries[skill] = entry

    category_summaries = {}
    for category, values in sorted(per_category.items()):
        entry = metrics(values["tp"], values["fn"], values["fp"], values["tn"])
        entry["inconclusive"] = values["inc_pos"] + values["inc_neg"]
        entry["inconclusive_rate"] = ratio(
            entry["inconclusive"],
            sum(values[key] for key in ("tp", "fn", "fp", "tn", "inc_pos", "inc_neg")),
        )
        category_summaries[category] = entry

    return {
        "overall": overall,
        "per_skill": skill_summaries,
        "per_category": category_summaries,
        "per_query": per_query,
        "unstable_queries": [
            query for query in per_query
            if query["valid_trials"] >= 2 and not query["stable"]
        ],
        "inconclusive_reasons": inconclusive_reasons(result),
    }


def infer_split(path: Path) -> str:
    """Infer a report split label from a result filename.

    中文：从文件名识别 train、validation 或 smoke；无法判断时返回 other。
    """
    name = path.name.casefold()
    if "validation" in name or "val" in name:
        return "validation"
    if "train" in name:
        return "train"
    if "smoke" in name:
        return "smoke"
    return "other"


def skills_digest() -> str:
    """Hash current skill resources for freshness comparisons.

    中文：按稳定路径顺序哈希当前 skill 树，忽略缓存文件。
    """
    digest = hashlib.sha256()
    for path in sorted((ROOT / "skills").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def result_freshness(result: dict, split: str, current_skills_sha: str) -> dict:
    """Compare recorded result digests with the current repository state.

    Design/System considerations: Dataset and skill freshness are independent controls. A matching
    dataset hash does not make results current when skill bytes changed, and legacy results without
    a Codex version are reported as unknown rather than assumed compatible.
    中文：比较结果中的 skill/dataset/runner 摘要与当前文件，保留 Codex 版本信息。

    设计/系统考虑：dataset 与 skill freshness 独立判断；数据集匹配不能覆盖 skill 变化，旧结果缺少
    Codex 版本时显示 unknown，不能假设兼容。
    """
    recorded_skills_sha = result.get("skills_sha256")
    dataset = ROOT / "evals" / f"{split}_queries.json"
    current_dataset_sha = hashlib.sha256(dataset.read_bytes()).hexdigest() if dataset.is_file() else None
    recorded_dataset_sha = result.get("dataset_sha256")
    recorded_runner_sha = result.get("runner_sha256")
    current_runner_sha = runner_digest()
    return {
        "recorded_runner_sha256": recorded_runner_sha,
        "current_runner_sha256": current_runner_sha,
        "runner_matches_current": (
            recorded_runner_sha == current_runner_sha if recorded_runner_sha is not None else None
        ),
        "codex_version": result.get("codex_version"),
        "model": result.get("model"),
        "recorded_skills_sha256": recorded_skills_sha,
        "current_skills_sha256": current_skills_sha,
        "skills_match_current": recorded_skills_sha == current_skills_sha,
        "recorded_dataset_sha256": recorded_dataset_sha,
        "current_dataset_sha256": current_dataset_sha,
        "dataset_matches_current": (
            recorded_dataset_sha == current_dataset_sha
            if recorded_dataset_sha is not None and current_dataset_sha is not None
            else None
        ),
    }


def load_entries(paths: list[Path], labels: list[str], excluded_ids: set[str] | None = None) -> list[dict]:
    """Load, optionally filter, summarize, and freshness-check result files.

    中文：读取结果，按需排除历史 case ID，并附加 split、summary 与 freshness。
    """
    entries = []
    current_skills_sha = skills_digest()
    found_excluded: set[str] = set()
    for index, path in enumerate(paths):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            print(f"{path}: cannot read result JSON: {exc}", file=sys.stderr)
            raise SystemExit(2)
        split = labels[index] if index < len(labels) else infer_split(path)
        if excluded_ids:
            found_excluded.update(row.get("id") for row in data["results"] if row.get("id") in excluded_ids)
            data = {**data, "results": [
                row for row in data["results"] if row.get("id") not in excluded_ids
            ]}
        entries.append({
            "file": str(path),
            "split": split,
            "freshness": result_freshness(data, split, current_skills_sha),
            "summary": compute_summary(data),
        })
    missing = (excluded_ids or set()) - found_excluded
    if missing:
        print(f"excluded case IDs not found: {', '.join(sorted(missing))}", file=sys.stderr)
        raise SystemExit(2)
    return entries


def format_text(entry: dict) -> str:
    """Render one summarized result as a human-readable text block.

    中文：格式化 freshness、总体指标、失败原因、skill 和 category 明细。
    """
    overall = entry["summary"]["overall"]

    def rate(value: float | None) -> str:
        """Format an optional metric with four decimal places.

        中文：将可选比率格式化为四位小数；None 显示为短横线。
        """
        return "-" if value is None else f"{value:.4f}"

    lines = [f"=== {entry['file']} [{entry['split']}] ==="]
    freshness = entry.get("freshness") or {}
    lines.append(
        "freshness: "
        f"skills={'current' if freshness.get('skills_match_current') else 'stale'} "
        f"dataset={('current' if freshness.get('dataset_matches_current') else 'stale') if freshness.get('dataset_matches_current') is not None else 'unknown'} "
        f"codex={freshness.get('codex_version') or 'unknown'} "
        f"runner={('current' if freshness.get('runner_matches_current') else 'stale') if freshness.get('runner_matches_current') is not None else 'unknown'} "
        f"model={freshness.get('model')}"
    )
    lines.append(
        f"decided={overall['decided']} coverage={rate(overall['coverage'])} "
        f"inconclusive={overall['inconclusive_total']} total={overall['total_trials']} "
        f"pass_rate={rate(overall['pass_rate'])}"
    )
    lines.append(f"TP={overall['tp']} FN={overall['fn']} FP={overall['fp']} TN={overall['tn']}")
    lines.append(
        f"precision={rate(overall['precision'])} recall={rate(overall['recall'])} "
        f"f1={rate(overall['f1'])} accuracy={rate(overall['accuracy'])}"
    )
    lines.append(
        f"FPR={rate(overall['false_positive_rate'])} FNR={rate(overall['false_negative_rate'])} "
        f"specificity={rate(overall['specificity'])} "
        f"balanced_acc={rate(overall['balanced_accuracy'])} "
        f"inconclusive_rate={rate(overall['inconclusive_rate'])}"
    )
    duration = overall.get("duration_seconds") or {}
    lines.append(
        f"time/session: mean={duration.get('mean')}s median={duration.get('median')}s "
        f"p95={duration.get('p95')}s min={duration.get('min')}s max={duration.get('max')}s "
        f"tps={overall.get('tokens_per_second')} out/s"
    )
    usage = overall.get("usage") or {}
    lines.append(
        "tokens: "
        f"input={usage.get('input_tokens')} cached={usage.get('cached_input_tokens')} "
        f"output={usage.get('output_tokens')} total={usage.get('reported_total_tokens')}"
    )
    unstable = entry["summary"].get("unstable_queries") or []
    if unstable:
        lines.append(
            "unstable queries: "
            + ", ".join(
                f"{query['id']}={query['trigger_rate']}"
                for query in unstable
            )
        )
    reasons = entry["summary"]["inconclusive_reasons"]
    if reasons:
        lines.append(
            "inconclusive reasons: "
            + ", ".join(f"{name}={count}" for name, count in sorted(reasons.items()))
        )
    for skill, values in entry["summary"]["per_skill"].items():
        lines.append(
            f"  {skill:28s} P={rate(values['precision'])} R={rate(values['recall'])} "
            f"F1={rate(values['f1'])} acc={rate(values['accuracy'])} "
            f"inc={values['inconclusive']}({rate(values['inconclusive_rate'])}) "
            f"t={values['mean_duration_seconds']}s p95={values['p95_duration_seconds']}s"
        )
    for category, values in entry["summary"].get("per_category", {}).items():
        lines.append(
            f"  category:{category:19s} P={rate(values['precision'])} "
            f"R={rate(values['recall'])} F1={rate(values['f1'])} "
            f"spec={rate(values['specificity'])} inc={values['inconclusive']}"
        )
    return "\n".join(lines)


def gap_metrics(first: dict, second: dict) -> dict:
    """Return first-minus-second metric deltas for two summaries.

    中文：计算两个 split 的 F1、precision、recall、accuracy、specificity 和不可判定率差值。
    """
    a = first["summary"]["overall"]
    b = second["summary"]["overall"]

    def diff(key: str) -> float | None:
        """Subtract one optional metric from its counterpart.

        中文：仅在两侧指标都有值时计算四位小数差值，否则返回 None。
        """
        left, right = a.get(key), b.get(key)
        if left is None or right is None:
            return None
        return round(left - right, 4)

    return {
        "delta_f1": diff("f1"),
        "delta_precision": diff("precision"),
        "delta_recall": diff("recall"),
        "delta_accuracy": diff("accuracy"),
        "delta_specificity": diff("specificity"),
        "delta_inconclusive_rate": diff("inconclusive_rate"),
    }


def main() -> int:
    """Summarize result files as text or JSON and optionally write output.

    中文：解析结果路径与标签，输出确定性指标，并按需写入 JSON summary 文件。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path, help="activation result JSON files")
    parser.add_argument("--json", action="store_true", help="emit one JSON array to stdout")
    parser.add_argument("--output", type=Path, help="write the JSON summaries to this file")
    parser.add_argument(
        "--label",
        action="append",
        help="split label for each file, in order; defaults to filename inference",
    )
    args = parser.parse_args()
    if not args.files:
        parser.error("at least one result file is required")
    if args.label and len(args.label) > len(args.files):
        parser.error("more --label values than files")

    entries = load_entries(args.files, args.label or [])

    if args.json:
        text = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
    else:
        text = "\n\n".join(format_text(entry) for entry in entries) + "\n"
        if len(entries) >= 2:
            gap = gap_metrics(entries[0], entries[1])
            text += (
                f"gap: dF1={gap['delta_f1']} dP={gap['delta_precision']} "
                f"dR={gap['delta_recall']} dAcc={gap['delta_accuracy']} "
                f"dSpec={gap['delta_specificity']} dIR={gap['delta_inconclusive_rate']}\n"
            )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

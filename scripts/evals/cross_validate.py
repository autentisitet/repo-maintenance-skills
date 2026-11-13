#!/usr/bin/env python3
"""Run the same eval under multiple models and compare where errors disappear.

Model selection is never hard-coded here: pass one or more ``--model`` values and
this tool runs the standard activation runner once per model into separate result
files, then prints a per-case outcome matrix plus a summary of which errors vanish
or appear when the model changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def model_slug(model: str) -> str:
    """Build a filesystem-safe, collision-resistant model identifier.

    Design/System considerations: A strict filename alphabet blocks path separators on POSIX and
    Windows, while a truncated SHA-256 suffix distinguishes names that normalize to the same text.
    中文：把模型名转换为安全文件名前缀，并附加摘要避免名称碰撞。

    设计/系统考虑：白名单字符同时阻断 POSIX/Windows 路径分隔符，SHA-256 后缀用于区分归一化后
    相同的模型名。
    """
    prefix = re.sub(r"[^A-Za-z0-9_-]+", "-", model).strip("-_")[:48] or "model"
    digest = hashlib.sha256(model.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"


def result_path(output_dir: Path, dataset: Path, model: str) -> Path:
    """Return the result path for one dataset and model.

    中文：根据输出目录、数据集名和模型标识生成单模型结果路径。
    """
    return output_dir / f"cross-{dataset.stem}-{model_slug(model)}.json"


def run_model(
    dataset: Path,
    model: str,
    output_dir: Path,
) -> tuple[Path, int]:
    """Run the activation evaluator once for a selected model.

    中文：组装并执行单模型评测命令，返回结果路径和子进程退出码。
    """
    output = result_path(output_dir, dataset, model)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "scripts.evals.run_activation_evals",
        str(dataset),
        "--allow-model-calls",
        "--runs",
        "1",
        "--jobs",
        "1",
        "--timeout",
        "300",
        "--model",
        model,
        "--output",
        str(output),
    ]
    completed = subprocess.run(command, cwd=ROOT)
    return output, completed.returncode


def case_errors(row: dict) -> set[str]:
    """Return the non-clean outcome labels for one case.

    中文：把一条 case 的 trial 归并为 FN、FP 或基础设施失败标签集合。
    """
    should = bool(row.get("should_trigger"))
    errors: set[str] = set()
    for trial in row.get("trials", []):
        status = trial.get("status")
        if status == "pass":
            continue
        if status == "fail":
            errors.add("fp" if not should else "fn")
        elif trial.get("infrastructure_failure"):
            errors.add(str(trial.get("reason") or "unavailable"))
        else:
            errors.add("fn" if should else "inc_neg")
    return errors


def load_results(models: list[str], output_dir: Path, dataset: Path) -> dict[str, dict]:
    """Load result payloads for every requested model.

    中文：读取各模型对应的结果 JSON；缺失或不可读时以退出码 2 终止。
    """
    results: dict[str, dict] = {}
    for model in models:
        path = result_path(output_dir, dataset, model)
        try:
            results[model] = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            print(f"{path}: cannot read result -> {exc}", file=sys.stderr)
            raise SystemExit(2)
    return results


def compare(models: list[str], output_dir: Path, dataset: Path) -> int:
    """Print per-case outcomes and differences from the baseline model.

    中文：比较多个模型的 case 级错误，输出消失和新增的错误类型统计。
    """
    results = load_results(models, output_dir, dataset)
    rows = results[models[0]].get("results", [])
    errors_by_model: dict[str, dict[str, set[str]]] = {
        model: {row.get("id"): case_errors(row) for row in results[model].get("results", [])}
        for model in models
    }

    print(f"\ncross-validation of {dataset.name} over {', '.join(models)}")
    print("case\t\t" + "\t".join(f"[{model_slug(model)}]" for model in models))
    for row in rows:
        case_id = str(row.get("id") or "?")
        outcomes = []
        for model in models:
            errors = errors_by_model[model].get(case_id, set())
            outcomes.append("ok" if not errors else ",".join(sorted(errors)))
        print(f"{case_id}\t\t" + "\t".join(outcomes))

    print("\nsummary (cases with >=1 error):")
    baseline = errors_by_model[models[0]]
    for model in models:
        errors = errors_by_model[model]
        print(f"  {model}: {sum(bool(e) for e in errors.values())} case(s) with errors")

    for model in models[1:]:
        disappeared = {
            kind: sum(
                kind in baseline[case_id] and kind not in errors_by_model[model].get(case_id, set())
                for case_id in baseline
            )
            for kind in ("fn", "fp", "timeout", "process_failed", "completion_missing", "unavailable")
        }
        introduced = {
            kind: sum(
                kind in errors_by_model[model].get(case_id, set()) and kind not in baseline[case_id]
                for case_id in baseline
            )
            for kind in ("fn", "fp", "timeout", "process_failed", "completion_missing", "unavailable")
        }
        print(f"\n  vs {models[0]}:")
        print(f"    disappeared: { {k: v for k, v in disappeared.items() if v} }")
        print(f"    introduced:  { {k: v for k, v in introduced.items() if v} }")
    return 0


def main() -> int:
    """Run or compare cross-model activation evaluations.

    中文：解析运行参数和 compare-only 模式，执行评测后输出比较结果。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--model", action="append", required=True, help="repeatable; first is the baseline")
    parser.add_argument("--output-dir", type=Path, default=Path("evals/results"))
    parser.add_argument("--compare-only", action="store_true", help="skip running; compare existing files")
    parser.add_argument("--allow-model-calls", action="store_true", help="required to run the models")
    args = parser.parse_args()

    if not args.allow_model_calls and not args.compare_only:
        parser.error("explicit --allow-model-calls is required to run models")

    models = args.model
    if len(set(models)) != len(models):
        parser.error("duplicate --model values")

    if not args.compare_only:
        for model in models:
            output, code = run_model(args.dataset, model, args.output_dir)
            print(f"{model}: wrote {output} (runner exit {code})", file=sys.stderr)
            if code == 2:
                print(f"{model}: runner aborted in preflight; comparison may be incomplete", file=sys.stderr)

    return compare(models, args.output_dir, args.dataset)


if __name__ == "__main__":
    raise SystemExit(main())

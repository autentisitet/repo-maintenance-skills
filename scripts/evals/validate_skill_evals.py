#!/usr/bin/env python3
"""Validate stable train/validation routing eval sets for repository skills."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"
DEFAULT_FILES = (ROOT / "evals/train_queries.json", ROOT / "evals/validation_queries.json")
SPLITS = {"train", "validation"}
CATEGORIES = {"direct", "indirect", "embedded", "boundary"}
SECRET_RE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{16,}|"
    r"(?:api[_-]?key|token|password|authorization)\s*[:=]\s*[^ <$\n]{8,})",
    re.IGNORECASE,
)
MIN_PER_LABEL = 8


def fail(message: str, errors: list[str]) -> None:
    """Append one validation failure to the shared error list.

    中文：追加一条数据集校验错误，但不中断其余检查。
    """
    errors.append(message)


def load_file(path: Path, errors: list[str]) -> tuple[str | None, list[dict[str, object]]]:
    """Load one eval dataset and return its split and query rows.

    中文：读取单个评测 JSON；格式错误写入 errors，并返回可继续处理的空结果。
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path}: cannot read JSON -> {exc}", errors)
        return None, []
    if not isinstance(data, dict):
        fail(f"{path}: top-level value must be an object", errors)
        return None, []
    split = data.get("split")
    queries = data.get("queries")
    if split not in SPLITS:
        fail(f"{path}: split must be train or validation", errors)
        split = None
    if not isinstance(queries, list):
        fail(f"{path}: queries must be an array", errors)
        return split, []
    return split, queries


def main() -> int:
    """Validate train and validation query files and print a summary.

    中文：执行跨文件覆盖率、重复项、标签和划分比例检查，并返回进程退出码。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path, default=list(DEFAULT_FILES))
    parser.add_argument("--json", action="store_true", help="write the summary as JSON")
    args = parser.parse_args()

    skills = {path.name for path in SKILLS_DIR.iterdir() if (path / "SKILL.md").is_file()}
    errors: list[str] = []
    ids: set[str] = set()
    prompts: set[str] = set()
    counts: dict[str, dict[bool, int]] = defaultdict(lambda: defaultdict(int))
    split_counts: dict[str, dict[str, dict[bool, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    total = 0

    for path in args.files:
        split, queries = load_file(path, errors)
        if split is None:
            continue
        for index, case in enumerate(queries, start=1):
            location = f"{path}:{index}"
            if not isinstance(case, dict):
                fail(f"{location}: query must be an object", errors)
                continue
            case_id = case.get("id")
            skill = case.get("skill")
            query = case.get("query")
            label = case.get("should_trigger")
            category = case.get("category")
            if not isinstance(case_id, str) or not case_id:
                fail(f"{location}: missing id", errors)
            elif case_id in ids:
                fail(f"{location}: duplicate id -> {case_id}", errors)
            else:
                ids.add(case_id)
            if skill not in skills:
                fail(f"{location}: unknown skill -> {skill}", errors)
                continue
            if category not in CATEGORIES:
                fail(f"{location}: category must be one of {', '.join(sorted(CATEGORIES))}", errors)
            if not isinstance(query, str) or not query.strip():
                fail(f"{location}: query must not be empty", errors)
                continue
            normalized = " ".join(query.casefold().split())
            if normalized in prompts:
                fail(f"{location}: query duplicates another split or case", errors)
            prompts.add(normalized)
            if SECRET_RE.search(query):
                fail(f"{location}: query appears to contain a real credential", errors)
            if not isinstance(label, bool):
                fail(f"{location}: should_trigger must be boolean", errors)
                continue
            counts[skill][label] += 1
            split_counts[split][skill][label] += 1
            total += 1

    for skill in sorted(skills):
        for label in (True, False):
            if counts[skill][label] < MIN_PER_LABEL:
                fail(
                    f"{skill}: should_trigger={str(label).lower()} requires at least {MIN_PER_LABEL} cases; "
                    f"found {counts[skill][label]}",
                    errors,
                )
            for split in SPLITS:
                if split_counts[split][skill][label] == 0:
                    fail(f"{skill}: {split} lacks should_trigger={str(label).lower()} cases", errors)

    train_total = sum(sum(labels.values()) for labels in split_counts["train"].values())
    ratio = train_total / total if total else 0
    if total and not 0.55 <= ratio <= 0.65:
        fail(f"train ratio must be 55%-65%; found {ratio:.1%}", errors)

    summary = {
        "ok": not errors,
        "queries": total,
        "skills": len(skills),
        "train_ratio": round(ratio, 4),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    else:
        print(f"Validated {total} routing evals across {len(skills)} skills; train ratio {ratio:.1%}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

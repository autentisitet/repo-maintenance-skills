#!/usr/bin/env python3
"""Validate skill eval coverage without claiming model behavior was tested."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
EVALS_FILE = ROOT / "evals" / "cases.yaml"
CATEGORIES = {"direct", "indirect", "incomplete", "negative", "edge"}


def main() -> int:
    data = yaml.safe_load(EVALS_FILE.read_text(encoding="utf-8"))
    cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(cases, list):
        print("evals/cases.yaml: cases 必须是 list", file=sys.stderr)
        return 1

    skills = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
    coverage: dict[str, set[str]] = defaultdict(set)
    ids: set[str] = set()
    errors: list[str] = []

    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"case {index}: 必须是 mapping")
            continue
        case_id = case.get("id")
        skill = case.get("skill")
        category = case.get("category")
        prompt = case.get("prompt")
        expected = case.get("expected")
        should_trigger = case.get("should_trigger")

        if not isinstance(case_id, str) or not case_id:
            errors.append(f"case {index}: 缺少 id")
        elif case_id in ids:
            errors.append(f"case {index}: id 重复 -> {case_id}")
        else:
            ids.add(case_id)
        if skill not in skills:
            errors.append(f"{case_id}: 未知 skill -> {skill}")
            continue
        if category not in CATEGORIES:
            errors.append(f"{case_id}: 未知 category -> {category}")
            continue
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{case_id}: prompt 不能为空")
        if not isinstance(expected, str) or not expected.strip():
            errors.append(f"{case_id}: expected 不能为空")
        if not isinstance(should_trigger, bool):
            errors.append(f"{case_id}: should_trigger 必须是 bool")
        elif category == "negative" and should_trigger:
            errors.append(f"{case_id}: negative 用例不得触发 skill")
        coverage[skill].add(category)

    for skill in sorted(skills):
        missing = CATEGORIES - coverage[skill]
        if missing:
            errors.append(f"{skill}: 缺少 eval 类别 -> {', '.join(sorted(missing))}")

    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"{len(cases)} 个 eval 用例覆盖 {len(skills)} 个 skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

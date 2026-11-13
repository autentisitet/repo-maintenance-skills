#!/usr/bin/env python3
"""Extract cases that still need a retry from an activation result file.

Infrastructure-inconclusive trials (timeout, process failure, missing completion,
unavailable evaluation) carry no routing evidence. This tool writes a small dataset
containing only those cases, so the standard runner can re-run them without touching
the full dataset. The original result file is never modified; merge the retry output
back explicitly so the retry stays auditable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REASONS = {
    "timeout",
    "agent_process_failed",
    "completion_event_missing",
    "evaluation_unavailable",
}


def retry_cases(result: dict, dataset: dict, reasons: set[str], min_trials: int) -> list[dict]:
    """Select source queries with enough matching infrastructure failures.

    中文：按失败原因和最少 trial 数，从原始数据集中筛选需要重试的 query。
    """
    by_id = {query["id"]: query for query in dataset.get("queries", [])}
    order = {query["id"]: index for index, query in enumerate(dataset.get("queries", []))}
    needs: dict[str, int] = {}
    for row in result.get("results", []):
        case_id = row.get("id")
        if not isinstance(case_id, str):
            continue
        count = 0
        for trial in row.get("trials", []):
            if (
                trial.get("status") == "inconclusive"
                and trial.get("infrastructure_failure")
                and trial.get("reason") in reasons
            ):
                count += 1
        if count >= min_trials:
            needs[case_id] = count
    selected = [by_id[case_id] for case_id in needs if case_id in by_id]
    selected.sort(key=lambda query: order.get(query["id"], 0))
    return selected


def main() -> int:
    """Write a retry dataset from activation results and source queries.

    中文：解析输入文件和筛选条件，将符合条件的 query 写入独立重试 JSON。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="activation result JSON")
    parser.add_argument("dataset", type=Path, help="source query-set JSON")
    parser.add_argument("output", type=Path, help="small retry dataset to write")
    parser.add_argument(
        "--reason",
        action="append",
        choices=sorted(REASONS),
        help="infrastructure reason to retry; repeatable, defaults to timeout",
    )
    parser.add_argument(
        "--min-trials",
        type=int,
        default=1,
        help="retry a case only when at least this many trials failed (default 1)",
    )
    args = parser.parse_args()
    if args.min_trials < 1:
        parser.error("--min-trials must be positive")

    try:
        result = json.loads(args.result.read_text(encoding="utf-8"))
        dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read input -> {exc}", file=sys.stderr)
        return 1

    reasons = set(args.reason or ["timeout"])
    selected = retry_cases(result, dataset, reasons, args.min_trials)
    payload = {key: value for key, value in dataset.items() if key != "queries"}
    payload["queries"] = selected
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{len(selected)} case(s) need retry ({', '.join(sorted(reasons))}); "
        f"wrote {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

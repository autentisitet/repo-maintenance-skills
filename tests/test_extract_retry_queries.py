#!/usr/bin/env python3
"""Tests for retry-query extraction."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.evals import extract_retry_queries


class RetryExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        """Create a temporary directory for retry extraction fixtures.

        中文：为每个重试筛选测试创建并自动清理独立临时目录。
        """
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def test_extracts_timeout_cases_and_preserves_metadata(self) -> None:
        dataset = {
            "version": 1,
            "split": "train",
            "split_seed": 20261111,
            "queries": [
                {"id": "a-t01", "skill": "a", "category": "direct", "query": "q1", "should_trigger": True},
                {"id": "a-t02", "skill": "a", "category": "indirect", "query": "q2", "should_trigger": False},
                {"id": "b-t01", "skill": "b", "category": "boundary", "query": "q3", "should_trigger": False},
            ],
        }
        result = {
            "evaluation_kind": "observed_entrypoint_reads",
            "results": [
                {"id": "a-t01", "skill": "a", "should_trigger": True, "trials": [
                    {"status": "inconclusive", "infrastructure_failure": True, "reason": "timeout"},
                ]},
                {"id": "a-t02", "skill": "a", "should_trigger": False, "trials": [
                    {"status": "pass"},
                ]},
                {"id": "b-t01", "skill": "b", "should_trigger": False, "trials": [
                    {"status": "inconclusive", "infrastructure_failure": True,
                     "reason": "agent_process_failed"},
                ]},
            ],
        }
        selected = extract_retry_queries.retry_cases(result, dataset, {"timeout"}, 1)
        self.assertEqual([case["id"] for case in selected], ["a-t01"])

        output = self.directory / "retry.json"
        payload = {key: value for key, value in dataset.items() if key != "queries"}
        payload["queries"] = selected
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(written["split"], "train")
        self.assertEqual(written["split_seed"], 20261111)
        self.assertEqual([case["id"] for case in written["queries"]], ["a-t01"])

    def test_min_trials_gate(self) -> None:
        dataset = {"split": "train", "queries": [
            {"id": "a-t01", "skill": "a", "category": "direct", "query": "q1", "should_trigger": True},
        ]}
        result = {"results": [
            {"id": "a-t01", "skill": "a", "should_trigger": True, "trials": [
                {"status": "inconclusive", "infrastructure_failure": True, "reason": "timeout"},
                {"status": "inconclusive", "infrastructure_failure": True, "reason": "timeout"},
            ]},
        ]}
        self.assertEqual(extract_retry_queries.retry_cases(result, dataset, {"timeout"}, 3), [])
        self.assertEqual(len(extract_retry_queries.retry_cases(result, dataset, {"timeout"}, 2)), 1)


if __name__ == "__main__":
    unittest.main()

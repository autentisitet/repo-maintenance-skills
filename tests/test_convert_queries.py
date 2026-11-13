#!/usr/bin/env python3
"""Tests for JSON <-> CSV query-set conversion."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.evals import convert_queries


class ConvertQueriesTests(unittest.TestCase):
    def setUp(self) -> None:
        """Create a temporary directory for conversion fixtures.

        中文：为每个转换测试创建并自动清理独立临时目录。
        """
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def test_round_trip_preserves_metadata_and_queries(self) -> None:
        payload = {
            "version": 1,
            "split": "train",
            "split_seed": 20261111,
            "queries": [
                {
                    "id": "a-t01",
                    "skill": "a",
                    "category": "direct",
                    "query": "使用 a 的规则，包含,逗号和\"引号\"。",
                    "should_trigger": True,
                },
            ],
        }
        json_path = self.directory / "train_queries.json"
        csv_path = self.directory / "train_queries.csv"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        convert_queries.write_csv(csv_path, payload["queries"])
        read_back = convert_queries.read_csv(csv_path)
        self.assertEqual(read_back, payload["queries"])
        self.assertEqual(convert_queries.check(json_path, csv_path), [])

        restored = json_path.with_name("restored.json")
        convert_queries.write_json(
            restored,
            {"split": "train", "queries": read_back, **{k: v for k, v in payload.items() if k not in ("split", "queries")}},
        )
        self.assertEqual(
            json.loads(restored.read_text(encoding="utf-8")),
            payload,
        )

    def test_check_reports_field_mismatch(self) -> None:
        payload = {
            "split": "validation",
            "queries": [{
                "id": "a-v01",
                "skill": "a",
                "category": "boundary",
                "query": "边界查询",
                "should_trigger": False,
            }],
        }
        json_path = self.directory / "validation_queries.json"
        csv_path = self.directory / "validation_queries.csv"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        convert_queries.write_csv(csv_path, payload["queries"])
        convert_queries.write_csv(csv_path, [{
            "id": "a-v01",
            "skill": "a",
            "category": "boundary",
            "query": "被改过的查询",
            "should_trigger": False,
        }])
        self.assertTrue(convert_queries.check(json_path, csv_path))

    def test_parse_bool_accepts_excel_friendly_forms(self) -> None:
        for raw, expected in (
            ("true", True),
            ("FALSE", False),
            ("1", True),
            ("0", False),
        ):
            self.assertEqual(convert_queries.parse_bool(raw), expected)
        with self.assertRaises(ValueError):
            convert_queries.parse_bool("yes")

    def test_infer_split_from_filename(self) -> None:
        self.assertEqual(convert_queries.infer_split(Path("train_queries.csv")), "train")
        self.assertEqual(convert_queries.infer_split(Path("activation-val.csv")), "validation")
        self.assertIsNone(convert_queries.infer_split(Path("queries.csv")))

    def test_excel_formula_prefixes_are_escaped_and_round_trip(self) -> None:
        queries = [
            {
                "id": f"a-t{index:02d}",
                "skill": "a",
                "category": "direct",
                "query": value,
                "should_trigger": True,
            }
            for index, value in enumerate(
                ("=1+1", "+SUM(A1:A2)", "-2+3", "@SUM(A1)", "\tformula", "'literal"),
                start=1,
            )
        ]
        csv_path = self.directory / "queries.csv"
        convert_queries.write_csv(csv_path, queries)

        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            exported = list(csv.DictReader(handle))
        self.assertTrue(all(row["query"].startswith("'") for row in exported))
        self.assertEqual(convert_queries.read_csv(csv_path), queries)


if __name__ == "__main__":
    unittest.main()

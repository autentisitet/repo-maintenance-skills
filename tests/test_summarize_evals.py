#!/usr/bin/env python3
"""Verify routing metrics are derived deterministically from runner output."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.evals import summarize_evals


class ClassifyTests(unittest.TestCase):
    def test_routing_outcomes_are_classified(self) -> None:
        self.assertEqual(summarize_evals.classify({"status": "pass"}, True), "tp")
        self.assertEqual(summarize_evals.classify({"status": "pass"}, False), "tn")
        self.assertEqual(summarize_evals.classify({"status": "fail"}, False), "fp")
        self.assertEqual(summarize_evals.classify({"status": "fail"}, True), "fn")
        self.assertEqual(
            summarize_evals.classify(
                {"status": "inconclusive", "infrastructure_failure": True, "reason": "timeout"},
                True,
            ),
            "inc_pos",
        )
        self.assertEqual(
            summarize_evals.classify(
                {"status": "inconclusive", "infrastructure_failure": True, "reason": "timeout"},
                False,
            ),
            "inc_neg",
        )

    def test_positive_miss_without_infrastructure_is_a_false_negative(self) -> None:
        trial = {"status": "inconclusive", "observed_skill_read": False}
        self.assertEqual(summarize_evals.classify(trial, True), "fn")
        self.assertEqual(summarize_evals.classify(trial, False), "inc_neg")


class SummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        """Create a mixed routing-result fixture for summary tests.

        中文：准备同时覆盖 TP、FN、FP、TN 和基础设施不可判定的公共结果数据。
        """
        self.result = {
            "evaluation_kind": "observed_entrypoint_reads",
            "results": [
                {"id": "a-pos-1", "skill": "a", "category": "direct", "should_trigger": True, "trials": [
                    {"status": "pass", "observed_skill_read": True},
                    {"status": "inconclusive", "observed_skill_read": False},
                ]},
                {"id": "a-neg-1", "skill": "a", "category": "boundary", "should_trigger": False, "trials": [
                    {"status": "pass", "observed_skill_read": False},
                    {"status": "fail", "observed_skill_read": True},
                ]},
                {"id": "a-pos-2", "skill": "a", "category": "direct", "should_trigger": True, "trials": [
                    {"status": "inconclusive", "infrastructure_failure": True, "reason": "timeout"},
                ]},
                {"id": "a-neg-2", "skill": "a", "category": "boundary", "should_trigger": False, "trials": [
                    {"status": "inconclusive", "infrastructure_failure": True,
                     "reason": "agent_process_failed"},
                ]},
            ],
        }

    def test_overall_metrics_exclude_inconclusive_from_denominators(self) -> None:
        summary = summarize_evals.compute_summary(self.result)
        overall = summary["overall"]
        self.assertEqual(overall["tp"], 1)
        self.assertEqual(overall["fn"], 1)
        self.assertEqual(overall["fp"], 1)
        self.assertEqual(overall["tn"], 1)
        self.assertEqual(overall["inconclusive_total"], 2)
        self.assertEqual(overall["total_trials"], 6)
        self.assertEqual(overall["passes"], 2)
        self.assertEqual(overall["failures"], 1)
        self.assertEqual(overall["precision"], 0.5)
        self.assertEqual(overall["recall"], 0.5)
        self.assertEqual(overall["f1"], 0.5)
        self.assertEqual(overall["accuracy"], 0.5)
        self.assertEqual(overall["false_positive_rate"], 0.5)
        self.assertEqual(overall["false_negative_rate"], 0.5)
        self.assertEqual(overall["specificity"], 0.5)
        self.assertEqual(overall["balanced_accuracy"], 0.5)
        self.assertAlmostEqual(overall["inconclusive_rate"], 0.3333, places=4)
        self.assertAlmostEqual(overall["pass_rate"], 0.3333, places=4)

    def test_inconclusive_reasons_are_normalized(self) -> None:
        self.assertEqual(
            summarize_evals.compute_summary(self.result)["inconclusive_reasons"],
            {"process_failed": 1, "timeout": 1},
        )

    def test_legacy_subagent_events_are_ignored(self) -> None:
        result = {"results": [{
            "id": "a", "skill": "a", "should_trigger": True,
            "trials": [{"status": "pass", "subagent_events": [{"kind": "collab_agent_spawn_begin"}]}],
        }]}
        summary = summarize_evals.compute_summary(result)
        self.assertNotIn("subagent_spawns", summary["overall"])
        self.assertEqual(summary["overall"]["tp"], 1)

    def test_category_breakdown_preserves_routing_boundaries(self) -> None:
        categories = summarize_evals.compute_summary(self.result)["per_category"]
        self.assertEqual(categories["direct"]["tp"], 1)
        self.assertEqual(categories["direct"]["fn"], 1)
        self.assertEqual(categories["boundary"]["tn"], 1)
        self.assertEqual(categories["boundary"]["fp"], 1)

    def test_per_skill_matches_overall_for_a_single_skill(self) -> None:
        summary = summarize_evals.compute_summary(self.result)
        per_skill = summary["per_skill"]["a"]
        overall = summary["overall"]
        for key in ("tp", "fn", "fp", "tn", "precision", "recall", "f1", "accuracy"):
            self.assertEqual(per_skill[key], overall[key])
        self.assertEqual(per_skill["inconclusive"], 2)

    def test_per_skill_counts_do_not_bleed_across_skills(self) -> None:
        result = {
            "results": [
                {"id": "a-pos", "skill": "a", "should_trigger": True,
                 "trials": [{"status": "pass"}]},
                {"id": "b-pos", "skill": "b", "should_trigger": True,
                 "trials": [{"status": "pass"}, {"status": "pass"}]},
            ],
        }
        summary = summarize_evals.compute_summary(result)
        self.assertEqual(summary["per_skill"]["a"]["tp"], 1)
        self.assertEqual(summary["per_skill"]["b"]["tp"], 2)
        self.assertEqual(summary["overall"]["tp"], 3)

    def test_per_query_trigger_rate_excludes_infrastructure_failures(self) -> None:
        row = {
            "id": "a-pos",
            "skill": "a",
            "should_trigger": True,
            "trials": [
                {"status": "pass", "observed_skill_read": True},
                {"status": "inconclusive", "observed_skill_read": False},
                {"status": "inconclusive", "infrastructure_failure": True},
            ],
        }
        query = summarize_evals.query_metrics(row)
        self.assertEqual(query["loaded_trials"], 1)
        self.assertEqual(query["valid_trials"], 2)
        self.assertEqual(query["inconclusive_trials"], 1)
        self.assertEqual(query["trigger_rate"], 0.5)
        self.assertFalse(query["stable"])

    def test_reported_total_does_not_double_count_cached_input(self) -> None:
        result = {
            "results": [{
                "id": "a-pos", "skill": "a", "should_trigger": True,
                "trials": [{
                    "status": "pass",
                    "usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 20},
                }],
            }],
        }
        usage = summarize_evals.compute_summary(result)["overall"]["usage"]
        self.assertEqual(usage["reported_total_tokens"], 120)


class RatioTests(unittest.TestCase):
    def test_empty_denominator_is_none(self) -> None:
        self.assertIsNone(summarize_evals.ratio(1, 0))
        self.assertEqual(summarize_evals.ratio(1, 2), 0.5)


class SplitInferenceTests(unittest.TestCase):
    def test_infer_split_from_filenames(self) -> None:
        cases = {
            "activation-train.json": "train",
            "activation-validation.json": "validation",
            "activation-val.json": "validation",
            "codex-smoke.json": "smoke",
            "result.json": "other",
        }
        for name, expected in cases.items():
            self.assertEqual(summarize_evals.infer_split(Path(name)), expected)


class LoadEntriesTests(unittest.TestCase):
    def test_labels_override_inference_and_entries_are_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps({
                "results": [
                    {"id": "a-pos-1", "skill": "a", "should_trigger": True,
                     "trials": [{"status": "pass", "observed_skill_read": True}]},
                ],
            }), encoding="utf-8")
            entries = summarize_evals.load_entries([path], ["train"])
            self.assertEqual(entries[0]["split"], "train")
            self.assertEqual(entries[0]["summary"]["overall"]["tp"], 1)

    def test_freshness_detects_stale_skill_snapshot(self) -> None:
        freshness = summarize_evals.result_freshness(
            {"skills_sha256": "old", "dataset_sha256": "old", "codex_version": None},
            "other",
            "current",
        )
        self.assertFalse(freshness["skills_match_current"])
        self.assertIsNone(freshness["dataset_matches_current"])
        self.assertIsNone(freshness["runner_matches_current"])

    def test_load_entries_excludes_only_requested_historical_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activation-train.json"
            path.write_text(json.dumps({"results": [
                {"id": "retired", "skill": "a", "should_trigger": True,
                 "trials": [{"status": "fail"}]},
                {"id": "current", "skill": "a", "should_trigger": True,
                 "trials": [{"status": "pass"}]},
            ]}), encoding="utf-8")
            filtered = summarize_evals.load_entries([path], [], {"retired"})[0]
            self.assertEqual(filtered["summary"]["overall"]["total_trials"], 1)
            self.assertEqual(filtered["summary"]["overall"]["tp"], 1)
            with self.assertRaises(SystemExit):
                summarize_evals.load_entries([path], [], {"missing"})

    def test_freshness_compares_runner_bytes(self) -> None:
        self.assertTrue(summarize_evals.result_freshness(
            {"runner_sha256": summarize_evals.runner_digest()}, "other", "current"
        )["runner_matches_current"])
        self.assertFalse(summarize_evals.result_freshness(
            {"runner_sha256": "old"}, "other", "current"
        )["runner_matches_current"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for cross-model eval comparison helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.evals import cross_validate


class CrossValidateTests(unittest.TestCase):
    def test_cross_model_run_uses_one_serial_trial_and_fixed_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            cross_validate.subprocess, "run", return_value=mock.Mock(returncode=0)
        ) as run:
            output, code = cross_validate.run_model(
                Path("evals/validation_queries.json"), "example", Path(directory)
            )
        command = run.call_args.args[0]
        self.assertEqual(code, 0)
        self.assertEqual(output.parent, Path(directory))
        self.assertEqual(command[command.index("--runs") + 1], "1")
        self.assertEqual(command[command.index("--jobs") + 1], "1")
        self.assertEqual(command[command.index("--timeout") + 1], "300")
        self.assertNotIn("--tool-output-token-limit", command)
        self.assertNotIn("--no-early-stop", command)

    def test_model_slug_is_filesystem_safe(self) -> None:
        slug = cross_validate.model_slug(r"..\openai/gpt-5:mini")
        self.assertRegex(slug, r"^[A-Za-z0-9_-]+-[0-9a-f]{10}$")
        self.assertNotIn("/", slug)
        self.assertNotIn("\\", slug)
        self.assertNotIn("..", slug)

    def test_model_slug_does_not_collapse_distinct_model_names(self) -> None:
        self.assertNotEqual(
            cross_validate.model_slug("openai/gpt-5"),
            cross_validate.model_slug("openai:gpt-5"),
        )

    def test_case_errors_classifies_outcomes(self) -> None:
        positive = {"should_trigger": True, "trials": [
            {"status": "pass"},
            {"status": "fail"},
            {"status": "inconclusive", "infrastructure_failure": True, "reason": "timeout"},
            {"status": "inconclusive"},
        ]}
        self.assertEqual(
            cross_validate.case_errors(positive),
            {"fn", "timeout"},
        )
        negative = {"should_trigger": False, "trials": [
            {"status": "pass"},
            {"status": "fail"},
        ]}
        self.assertEqual(cross_validate.case_errors(negative), {"fp"})
        clean = {"should_trigger": True, "trials": [{"status": "pass"}]}
        self.assertEqual(cross_validate.case_errors(clean), set())


if __name__ == "__main__":
    unittest.main()

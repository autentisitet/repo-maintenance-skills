#!/usr/bin/env python3
"""Smoke-test chart rendering for activation eval summaries."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.evals import plot_evals, summarize_evals


def sample_result() -> dict:
    """Return a compact payload covering the main plot input states.

    中文：构造含 TP、FN、FP 和基础设施失败的最小绘图结果 fixture。
    """
    return {
        "evaluation_kind": "observed_entrypoint_reads",
        "results": [
            {"id": "a-pos", "skill": "a", "should_trigger": True, "trials": [
                {"status": "pass", "observed_skill_read": True},
                {"status": "inconclusive", "observed_skill_read": False},
                {"status": "inconclusive", "infrastructure_failure": True, "reason": "timeout"},
            ]},
            {"id": "a-neg", "skill": "a", "should_trigger": False, "trials": [
                {"status": "pass", "observed_skill_read": False},
                {"status": "fail", "observed_skill_read": True},
            ]},
            {"id": "b-pos", "skill": "b", "should_trigger": True, "trials": [
                {"status": "pass", "observed_skill_read": True},
            ]},
        ],
    }


class ChartTests(unittest.TestCase):
    def setUp(self) -> None:
        """Create a temporary output directory for generated charts.

        中文：为每个绘图测试创建并自动清理独立输出目录。
        """
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def assert_png(self, path: Path) -> None:
        """Assert that a chart path contains a non-empty PNG file.

        中文：检查图表文件存在且大小非零，避免只验证函数未抛异常。
        """
        self.assertTrue(path.is_file(), f"missing chart: {path}")
        self.assertGreater(path.stat().st_size, 0, f"empty chart: {path}")

    def test_summary_charts_are_written(self) -> None:
        summary = summarize_evals.compute_summary(sample_result())
        plot_evals.confusion_matrix(summary, self.directory / "confusion.png")
        plot_evals.per_skill_bars(summary, self.directory / "per-skill.png")
        plot_evals.per_skill_errors(summary, self.directory / "per-skill-errors.png")
        plot_evals.inconclusive_bars(summary, self.directory / "inconclusive.png")
        plot_evals.trigger_rate_distribution(summary, self.directory / "trigger-rate.png")
        for name in ("confusion.png", "per-skill.png", "per-skill-errors.png",
                     "inconclusive.png", "trigger-rate.png"):
            self.assert_png(self.directory / name)

    def test_undefined_error_rate_is_not_drawn_as_zero(self) -> None:
        summary = summarize_evals.compute_summary(sample_result())
        with mock.patch.object(plot_evals.plt, "close"):
            plot_evals.per_skill_errors(summary, self.directory / "errors.png")
            fig = plot_evals.plt.gcf()
            ax = fig.axes[0]
            self.assertIn("N/A", [text.get_text() for text in ax.texts])
            self.assertIn("neg=0", [label.get_text() for label in ax.get_yticklabels()][1])
        plot_evals.plt.close(fig)

    def test_trend_chart_is_written(self) -> None:
        entries = [
            {"split": "train", "summary": summarize_evals.compute_summary(sample_result())},
            {"split": "validation", "summary": summarize_evals.compute_summary(sample_result())},
        ]
        plot_evals.iteration_trend(entries, self.directory / "trend.png")
        self.assert_png(self.directory / "trend.png")

    def test_one_snapshot_per_split_is_a_comparison_not_an_iteration(self) -> None:
        entries = [
            {"split": split, "summary": summarize_evals.compute_summary(sample_result())}
            for split in ("train", "validation")
        ]
        with mock.patch.object(plot_evals.plt, "close"):
            plot_evals.iteration_trend(entries, self.directory / "comparison.png")
            fig = plot_evals.plt.gcf()
            self.assertTrue(all(ax.get_xlabel() != "iteration" for ax in fig.axes))
            self.assertTrue(all(ax.patches for ax in fig.axes))
        plot_evals.plt.close(fig)

    def test_radar_chart_is_written_for_three_or_more_skills(self) -> None:
        summary = {
            "per_skill": {
                "a": {"precision": 0.9, "recall": 0.8, "f1": 0.85},
                "b": {"precision": 0.7, "recall": 0.9, "f1": 0.79},
                "c": {"precision": 1.0, "recall": 0.6, "f1": 0.75},
                "d": {"precision": 0.85, "recall": 0.85, "f1": 0.85},
            },
        }
        self.assertTrue(
            plot_evals.radar_chart(summary, self.directory / "radar.png", label="train")
        )
        self.assert_png(self.directory / "radar.png")

    def test_radar_chart_skips_with_fewer_than_three_skills(self) -> None:
        summary = {
            "per_skill": {
                "a": {"precision": 0.9, "recall": 0.8, "f1": 0.85},
                "b": {"precision": 0.7, "recall": 0.9, "f1": 0.79},
            },
        }
        self.assertFalse(
            plot_evals.radar_chart(summary, self.directory / "radar.png")
        )


if __name__ == "__main__":
    unittest.main()

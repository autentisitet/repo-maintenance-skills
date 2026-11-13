#!/usr/bin/env python3
"""Tests for activation evidence, sampling, and incremental output."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from scripts.evals import run_activation_evals as activation
from scripts.evals.check_skill_discovery import link_project_skills


class ActivationEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        """Create one isolated skill fixture and patch the runner root.

        中文：为每个测试创建临时 skill，并把 activation ROOT 指向该隔离目录。
        """
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill = self.root / "skills" / "sample-skill"
        self.skill.mkdir(parents=True)
        self.content = (
            "---\nname: sample-skill\ndescription: Test activation evidence.\n---\n"
            "# Sample Skill\n\nFollow the workflow.\n"
        )
        (self.skill / "SKILL.md").write_text(self.content, encoding="utf-8")
        patcher = mock.patch.object(activation, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def event(command: str, output: str, exit_code: int = 0) -> str:
        """Build one command-execution JSONL event fixture.

        中文：生成带命令、聚合输出和退出码的 item.completed 测试事件。
        """
        return json.dumps({
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": command,
                "aggregated_output": output,
                "exit_code": exit_code,
            },
        })

    def test_complete_successful_entrypoint_read_is_evidence(self) -> None:
        stream = "\n".join([
            self.event("cat .agents/skills/sample-skill/SKILL.md", self.content),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "secret": "x"}}),
        ])
        result = activation.observe(stream)
        self.assertEqual(result["observed_reads"], ["sample-skill"])
        self.assertTrue(result["turn_completed"])
        self.assertEqual(result["usage"], {"input_tokens": 10})

    def test_self_report_failed_command_and_partial_output_are_not_evidence(self) -> None:
        cases = (
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": self.content}}),
            self.event("cat SKILL.md", self.content, exit_code=1),
            self.event("head SKILL.md", "---\nname: sample-skill\n---\n"),
        )
        for stream in cases:
            with self.subTest(stream=stream[:30]):
                self.assertEqual(activation.observe(stream)["observed_reads"], [])

    def test_sampling_is_deterministic_per_skill_and_label(self) -> None:
        cases = [
            {"id": "b-2", "skill": "b", "should_trigger": False},
            {"id": "a-2", "skill": "a", "should_trigger": True},
            {"id": "a-1", "skill": "a", "should_trigger": True},
            {"id": "a-n", "skill": "a", "should_trigger": False},
            {"id": "b-1", "skill": "b", "should_trigger": False},
        ]
        self.assertEqual(
            [case["id"] for case in activation.sample_cases(cases, 1)],
            ["a-1", "a-n", "b-1"],
        )

    def test_query_sha256_tracks_query_content(self) -> None:
        base = {"id": "a-1", "skill": "a", "category": "direct",
                "query": "q", "should_trigger": True}
        changed = dict(base, query="q changed")
        self.assertEqual(activation.query_sha256(base), activation.query_sha256(base))
        self.assertNotEqual(activation.query_sha256(base), activation.query_sha256(changed))

    def test_reliable_routing_mismatch_is_a_failure(self) -> None:
        self.assertEqual(activation.outcome_status(False, True), "fail")
        self.assertEqual(activation.outcome_status(True, False), "fail")
        self.assertEqual(activation.outcome_status(True, True), "pass")
        self.assertEqual(activation.outcome_status(False, False), "pass")

    def test_wait_process_until_terminates_after_timeout(self) -> None:
        process = mock.Mock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("codex", 1), 0]

        result = activation.wait_process_until(process, time.monotonic() + 1)

        self.assertIsNone(result)
        process.terminate.assert_called_once_with()

    def test_independent_session_disables_multi_agent(self) -> None:
        case = {"id": "sample-positive-01", "skill": "sample-skill",
                "query": "Use sample skill.", "should_trigger": True}
        with mock.patch.object(activation, "link_project_skills"), mock.patch.object(
            activation.subprocess, "Popen", side_effect=FileNotFoundError("codex")
        ) as launch:
            result = activation.run_case(case, timeout=1)
        command = launch.call_args.args[0]
        self.assertEqual(command[command.index("--disable") + 1], "multi_agent")
        self.assertIn("--ephemeral", command)
        self.assertEqual(result["reason"], "evaluation_unavailable")

    @unittest.skipIf(os.name == "nt", "select on pipes requires POSIX")
    def test_partial_jsonl_line_cannot_extend_timeout(self) -> None:
        case = {"id": "sample-positive-01", "skill": "sample-skill",
                "query": "Use sample skill.", "should_trigger": True}
        original_popen = subprocess.Popen

        def launch(*args, **kwargs):
            """Start a child that leaves an unterminated JSONL event on stdout.

            中文：模拟输出半行后持续运行的子进程，以验证 deadline 仍能终止它。
            """
            return original_popen(
                [sys.executable, "-c", "import sys,time; sys.stdout.write('{'); "
                 "sys.stdout.flush(); time.sleep(3)"],
                **kwargs,
            )

        start = time.monotonic()
        with mock.patch.object(activation, "link_project_skills"), mock.patch.object(
            activation.subprocess, "Popen", side_effect=launch
        ):
            result = activation.run_case(case, timeout=0.2, markers=[])
        self.assertEqual(result["reason"], "timeout")
        self.assertLess(time.monotonic() - start, 2)

    @unittest.skipIf(os.name == "nt", "select on pipes requires POSIX")
    def test_fragmented_jsonl_line_is_observed(self) -> None:
        case = {"id": "sample-positive-01", "skill": "sample-skill",
                "query": "Use sample skill.", "should_trigger": True}
        event = json.dumps(json.loads(self.event(
            "cat .agents/skills/sample-skill/SKILL.md", self.content + "中文"
        )), ensure_ascii=False)
        original_popen = subprocess.Popen

        def launch(*args, **kwargs):
            """Stream a valid JSONL event across a UTF-8 character boundary.

            中文：拆开多字节字符输出，验证增量解码和按行归约不会丢失证据。
            """
            encoded = (event + "\n").encode("utf-8")
            boundary = encoded.index("中".encode("utf-8")) + 1
            script = (
                "import sys,time; a,b=" + repr((encoded[:boundary], encoded[boundary:]))
                + "; sys.stdout.buffer.write(a); sys.stdout.buffer.flush(); "
                  "time.sleep(0.05); sys.stdout.buffer.write(b); sys.stdout.buffer.flush()"
            )
            return original_popen([sys.executable, "-c", script], **kwargs)

        with mock.patch.object(activation, "link_project_skills"), mock.patch.object(
            activation.subprocess, "Popen", side_effect=launch
        ):
            result = activation.run_case(case, timeout=2, markers=activation.load_skill_markers())
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["observed_reads"], ["sample-skill"])

    def test_subagent_events_are_not_recorded(self) -> None:
        event = json.dumps({"type": "collab_agent_spawn_begin", "thread_id": "other"})
        state = {"turn_completed": False, "usage": {}}
        activation.match_line(event, [], set(), state)
        self.assertNotIn("subagent_events", state)

    def test_previous_reuse_map_gates_on_model_and_decided_trials(self) -> None:
        case = {"id": "a-1", "skill": "a", "category": "direct",
                "query": "q", "should_trigger": True}
        output = self.root / "results.json"
        previous = {
            "evaluation_kind": "observed_entrypoint_reads",
            "runner_sha256": "runner-sha",
            "codex_version": "codex-cli 1.2.3",
            "model": "gpt-5.6-sol",
            "skills_sha256": "skills-sha",
            "results": [
                {"id": "a-1", "query_sha256": activation.query_sha256(case),
                 "trials": [{"status": "pass"}, {"status": "pass"}]},
            ],
        }
        output.write_text(json.dumps(previous), encoding="utf-8")

        self.assertEqual(
            activation.previous_reuse_map(
                output, "gpt-5.6-sol", "runner-sha",
                "codex-cli 1.2.3", "skills-sha", [case], 2
            ),
            {0: [{"status": "pass"}, {"status": "pass"}]},
        )
        self.assertEqual(
            activation.previous_reuse_map(
                output, "other-model", "runner-sha",
                "codex-cli 1.2.3", "skills-sha", [case], 2
            ),
            {},
        )

    def test_previous_reuse_map_skips_inconclusive_trials(self) -> None:
        case = {"id": "a-1", "skill": "a", "category": "direct",
                "query": "q", "should_trigger": True}
        output = self.root / "results.json"
        previous = {
            "evaluation_kind": "observed_entrypoint_reads",
            "runner_sha256": "runner-sha",
            "codex_version": "codex-cli 1.2.3",
            "model": "gpt-5.6-sol",
            "skills_sha256": "skills-sha",
            "results": [
                {"id": "a-1", "query_sha256": activation.query_sha256(case),
                 "trials": [{"status": "inconclusive", "infrastructure_failure": True,
                             "reason": "timeout"}, {"status": "pass"}]},
            ],
        }
        output.write_text(json.dumps(previous), encoding="utf-8")
        self.assertEqual(
            activation.previous_reuse_map(
                output, "gpt-5.6-sol", "runner-sha",
                "codex-cli 1.2.3", "skills-sha", [case], 2
            ),
            {},
        )

    def test_reuse_requires_matching_runner_bytes(self) -> None:
        case = {"id": "a-1", "skill": "a", "category": "direct",
                "query": "q", "should_trigger": True}
        output = self.root / "results.json"
        previous = {
            "evaluation_kind": "observed_entrypoint_reads",
            "codex_version": "codex-cli 1.2.3",
            "model": "gpt-5.6-sol",
            "skills_sha256": "skills-sha",
            "results": [{"id": "a-1", "query_sha256": activation.query_sha256(case),
                         "trials": [{"status": "pass"}]}],
        }
        for recorded_sha in (None, "different"):
            previous["runner_sha256"] = recorded_sha
            output.write_text(json.dumps(previous), encoding="utf-8")
            self.assertEqual(
                activation.previous_reuse_map(
                    output, "gpt-5.6-sol", "runner-sha",
                    "codex-cli 1.2.3", "skills-sha", [case], 1
                ),
                {},
            )

    def test_reuse_requires_same_codex_version(self) -> None:
        case = {"id": "a-1", "skill": "a", "category": "direct",
                "query": "q", "should_trigger": True}
        output = self.root / "results.json"
        output.write_text(json.dumps({
            "evaluation_kind": "observed_entrypoint_reads",
            "runner_sha256": "runner-sha",
            "codex_version": "codex-cli old",
            "model": "gpt-5.6-sol",
            "skills_sha256": "skills-sha",
            "results": [{
                "id": "a-1", "query_sha256": activation.query_sha256(case),
                "trials": [{"status": "pass"}],
            }],
        }), encoding="utf-8")
        self.assertEqual(
            activation.previous_reuse_map(
                output, "gpt-5.6-sol", "runner-sha",
                "codex-cli new", "skills-sha", [case], 1
            ),
            {},
        )

    @unittest.skipIf(os.name == "nt", "POSIX symlink assertion")
    def test_project_links_point_to_skill_sources(self) -> None:
        workspace = self.root / "workspace"
        workspace.mkdir()
        link_project_skills(workspace, self.root / "skills")
        self.assertEqual(
            (workspace / ".agents" / "skills" / "sample-skill").resolve(),
            self.skill.resolve(),
        )

    def test_preflight_infrastructure_failure_stops_remaining_trials(self) -> None:
        dataset = self.root / "queries.json"
        dataset.write_text(json.dumps({
            "split": "train",
            "queries": [{
                "id": "sample-positive-01",
                "skill": "sample-skill",
                "category": "direct",
                "query": "Use sample skill.",
                "should_trigger": True,
            }],
        }), encoding="utf-8")
        output = self.root / "results" / "activation.json"
        trial = {
            "status": "inconclusive",
            "infrastructure_failure": True,
            "reason": "agent_process_failed",
        }
        argv = [
            "run_activation_evals", str(dataset), "--allow-model-calls",
            "--runs", "3", "--output", str(output),
        ]
        with mock.patch.object(activation, "run_case", return_value=trial), mock.patch.object(
            sys, "argv", argv
        ):
            self.assertEqual(activation.main(), 2)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["completed_trials"], 1)
        self.assertEqual(payload["expected_trials"], 3)
        self.assertEqual(payload["results"][0]["category"], "direct")

    def test_preflight_failure_preserves_existing_output(self) -> None:
        dataset = self.root / "queries.json"
        dataset.write_text(json.dumps({"split": "train", "queries": [{
            "id": "sample-positive-01", "skill": "sample-skill",
            "category": "direct", "query": "Use sample skill.",
            "should_trigger": True,
        }]}), encoding="utf-8")
        output = self.root / "results.json"
        original = '{"historical": "keep this result"}\n'
        output.write_text(original, encoding="utf-8")
        trial = {"status": "inconclusive", "infrastructure_failure": True,
                 "reason": "agent_process_failed"}
        argv = ["run_activation_evals", str(dataset), "--allow-model-calls",
                "--runs", "3", "--output", str(output)]
        with mock.patch.object(activation, "run_case", return_value=trial), mock.patch.object(
            sys, "argv", argv
        ):
            self.assertEqual(activation.main(), 2)
        self.assertEqual(output.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()

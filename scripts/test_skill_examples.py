#!/usr/bin/env python3
"""Behavior tests for executable examples embedded in skills."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_section_dividers():
    path = ROOT / "skills" / "markdown-docs" / "scripts" / "section-dividers.py"
    spec = importlib.util.spec_from_file_location("section_dividers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def makefile_example() -> str:
    path = ROOT / "skills" / "container-quality" / "references" / "compose.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    inside = False
    selected: list[str] = []
    for line in lines:
        if line == "```makefile":
            inside = True
            continue
        if inside and line == "```":
            break
        if inside:
            selected.append(line)
    if not selected:
        raise AssertionError("Makefile example not found")
    return "\n".join(selected) + "\n"


class MarkdownToolTests(unittest.TestCase):
    def test_dividers_skip_fenced_headings_and_are_idempotent(self) -> None:
        module = load_section_dividers()
        source = (
            "# Demo\n\n## One\n\nText\n\n```markdown\n## Not a section\n```\n\n"
            "## Two\n\nMore\n"
        )
        formatted = module.format_markdown(source)
        self.assertEqual(formatted.count("\n---\n"), 1)
        self.assertIn("```markdown\n## Not a section\n```", formatted)
        self.assertEqual(module.format_markdown(formatted), formatted)


class ContainerExampleTests(unittest.TestCase):
    def test_makefile_selects_runtime_specific_cpu_and_gpu_files(self) -> None:
        example = makefile_example()
        example += '\nprint-selection:\n\t@printf "%s|%s|%s\\n" "$(COMPOSE)" "$(RUNTIME)" "$(COMPOSE_FILES)"\n'
        cases = (
            (
                "podman-compose",
                "0",
                "podman-compose|podman|-f deploy-config/compose/docker-compose.yaml "
                "-f deploy-config/compose/docker-compose.podman-cpu.yaml",
            ),
            (
                "podman compose",
                "1",
                "podman compose|podman|-f deploy-config/compose/docker-compose.yaml "
                "-f deploy-config/compose/docker-compose.podman-gpu.yaml",
            ),
            (
                "docker-compose",
                "false",
                "docker-compose|docker|-f deploy-config/compose/docker-compose.yaml "
                "-f deploy-config/compose/docker-compose.docker-cpu.yaml",
            ),
            (
                "docker compose",
                "yes",
                "docker compose|docker|-f deploy-config/compose/docker-compose.yaml "
                "-f deploy-config/compose/docker-compose.docker-gpu.yaml",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            makefile = Path(directory) / "Makefile"
            makefile.write_text(example, encoding="utf-8")
            for compose, gpu, expected in cases:
                result = subprocess.run(
                    ["make", "--no-print-directory", "print-selection", f"COMPOSE={compose}", f"GPU={gpu}"],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.stdout.strip(), expected)

            default = subprocess.run(
                ["make", "--no-print-directory", "print-selection", "COMPOSE=podman-compose"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("docker-compose.podman-cpu.yaml", default.stdout)


if __name__ == "__main__":
    unittest.main()

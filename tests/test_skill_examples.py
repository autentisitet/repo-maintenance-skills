#!/usr/bin/env python3
"""Behavior tests for executable examples embedded in skills."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_section_dividers():
    """Load the Markdown divider script as a Python module.

    中文：按文件路径动态导入 section-dividers.py，供行为测试直接调用。
    """
    path = ROOT / "skills" / "markdown-docs" / "scripts" / "section-dividers.py"
    spec = importlib.util.spec_from_file_location("section_dividers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def makefile_example() -> str:
    """Extract the first Makefile example from the container reference.

    中文：读取 compose reference 中的 Makefile 围栏内容，供真实 make 行为测试使用。
    """
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


class RepositoryPreflightTests(unittest.TestCase):
    def test_remote_credentials_are_redacted(self) -> None:
        script = ROOT / "skills" / "github-repo-management" / "scripts" / "preflight.sh"
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(["git", "init", "-q", directory], check=True)
            subprocess.run(
                ["git", "-C", directory, "remote", "add", "origin", "https://user:secret@example.com/acme/repo.git"],
                check=True,
            )
            result = subprocess.run(
                [str(script), directory],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertNotIn("user:secret", result.stdout)
            self.assertIn("https://[redacted]@example.com/acme/repo.git", result.stdout)


class BilingualDocstringTests(unittest.TestCase):
    def test_production_and_helper_functions_have_bilingual_docstrings(self) -> None:
        paths = (
            sorted((ROOT / "scripts").rglob("*.py"))
            + sorted((ROOT / "skills").glob("*/scripts/*.py"))
            + sorted((ROOT / "tests").glob("*.py"))
        )
        missing: list[str] = []
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if path.parent.name == "tests" and node.name.startswith("test_"):
                    continue
                docstring = ast.get_docstring(node, clean=False)
                if docstring is None or "中文：" not in docstring:
                    missing.append(f"{path.relative_to(ROOT)}:{node.lineno}:{node.name}")
        self.assertEqual(missing, [])

    def test_design_consideration_sections_are_bilingual_pairs(self) -> None:
        paths = (
            sorted((ROOT / "scripts").rglob("*.py"))
            + sorted((ROOT / "skills").glob("*/scripts/*.py"))
            + sorted((ROOT / "tests").glob("*.py"))
        )
        unpaired: list[str] = []
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                docstring = ast.get_docstring(node, clean=False) or ""
                has_english = "Design/System considerations:" in docstring
                has_chinese = "设计/系统考虑：" in docstring
                chinese_start = docstring.find("中文：")
                english_design = docstring.find("Design/System considerations:")
                chinese_design = docstring.find("设计/系统考虑：")
                if (
                    has_english != has_chinese
                    or (has_english and not (english_design < chinese_start < chinese_design))
                    or (chinese_start >= 0 and any("\u4e00" <= char <= "\u9fff" for char in docstring[:chinese_start]))
                ):
                    unpaired.append(f"{path.relative_to(ROOT)}:{node.lineno}:{node.name}")
        self.assertEqual(unpaired, [])


if __name__ == "__main__":
    unittest.main()

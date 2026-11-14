#!/usr/bin/env python3
"""Exercise managed POSIX skill removal without touching the real Codex home."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts/links/install.sh"
UNINSTALL = ROOT / "scripts/links/uninstall.sh"


@unittest.skipIf(os.name == "nt", "POSIX symlinks and Bash are required")
class UninstallTests(unittest.TestCase):
    def setUp(self) -> None:
        """Set an isolated CODEX_HOME for each install/remove test.

        中文：每条测试都使用独立的临时 Codex 目录，避免接触真实安装。
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name) / "codex"
        self.environment = {**os.environ, "CODEX_HOME": str(self.home)}

    def run_script(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        """Invoke a Bash installer with the isolated home and capture its result.

        中文：只在临时安装目录执行 Bash 脚本，返回输出与退出码供断言。
        """
        return subprocess.run(
            ["bash", str(script), *args], env=self.environment,
            capture_output=True, text=True, check=False,
        )

    def test_uninstall_only_removes_own_links(self) -> None:
        self.assertEqual(self.run_script(INSTALL).returncode, 0)
        target = self.home / "skills/markdown-docs"
        other = self.home / "skills/custom-skill"
        other.mkdir()
        (other / "keep-me").write_text("personal", encoding="utf-8")
        self.assertTrue(target.is_symlink())
        self.assertEqual(self.run_script(UNINSTALL).returncode, 0)
        self.assertFalse(target.exists())
        self.assertFalse(target.is_symlink())
        self.assertEqual((other / "keep-me").read_text(encoding="utf-8"), "personal")
        self.assertEqual(self.run_script(UNINSTALL).returncode, 0)

    def test_uninstall_only_removes_marked_copies(self) -> None:
        self.assertEqual(self.run_script(INSTALL, "--copy").returncode, 0)
        target = self.home / "skills/markdown-docs"
        self.assertTrue((target / ".repo-maintenance-skills-install").is_file())
        self.assertEqual(self.run_script(UNINSTALL).returncode, 0)
        self.assertFalse(target.exists())

    def test_unmanaged_same_name_and_foreign_link_survive(self) -> None:
        target = self.home / "skills/markdown-docs"
        target.mkdir(parents=True)
        (target / "keep-me").write_text("personal", encoding="utf-8")
        foreign = self.home / "skills/repo-hygiene"
        foreign.symlink_to(target, target_is_directory=True)
        self.assertEqual(self.run_script(UNINSTALL).returncode, 0)
        self.assertEqual((target / "keep-me").read_text(encoding="utf-8"), "personal")
        self.assertTrue(foreign.is_symlink())

    def test_help_does_not_create_installation_directory(self) -> None:
        self.assertEqual(self.run_script(UNINSTALL, "--help").returncode, 0)
        self.assertFalse(self.home.exists())


if __name__ == "__main__":
    unittest.main()

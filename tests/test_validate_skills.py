#!/usr/bin/env python3
"""Regression tests for the repository skill validator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.packages.validate_skills import (
    check_links,
    check_openai_yaml,
    check_skill_resources,
    parse_frontmatter,
)


class ValidatorTests(unittest.TestCase):
    def test_invalid_frontmatter_yaml_is_rejected(self) -> None:
        text = "---\nname: demo\ndescription: [unterminated\n---\n# Demo\n"
        with self.assertRaises(ValueError):
            parse_frontmatter(text)

    def test_frontmatter_must_be_mapping(self) -> None:
        with self.assertRaises(ValueError):
            parse_frontmatter("---\n- demo\n---\n# Demo\n")

    def test_frontmatter_preserves_unknown_keys_for_compatibility(self) -> None:
        text = "---\nname: demo\ndescription: demo\nunknown: true\n---\n# Demo\n"
        self.assertTrue(parse_frontmatter(text)["unknown"])

    def test_invalid_openai_yaml_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "demo"
            config = skill / "agents" / "openai.yaml"
            config.parent.mkdir(parents=True)
            config.write_text("interface: [unterminated\n", encoding="utf-8")
            errors: list[str] = []
            check_openai_yaml(skill, "demo", errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("invalid YAML", errors[0])

    def test_markdown_parent_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skill"
            root.mkdir()
            (Path(directory) / "secret.txt").write_text("secret", encoding="utf-8")
            markdown = root / "SKILL.md"
            markdown.write_text("[outside](../secret.txt)\n", encoding="utf-8")
            errors: list[str] = []
            check_links(markdown, root, errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("path escapes", errors[0])

    def test_angle_bracket_link_with_spaces_cannot_bypass_boundary_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skill"
            root.mkdir()
            (Path(directory) / "secret file.txt").write_text("secret", encoding="utf-8")
            markdown = root / "SKILL.md"
            markdown.write_text("[outside](<../secret file.txt>)\n", encoding="utf-8")
            errors: list[str] = []
            check_links(markdown, root, errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("path escapes", errors[0])

    def test_escaping_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            skill = base / "skill"
            skill.mkdir()
            outside = base / "outside.txt"
            outside.write_text("secret", encoding="utf-8")
            (skill / "escape.txt").symlink_to(outside)
            errors: list[str] = []
            check_skill_resources(skill, errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("path escapes", errors[0])

    def test_symlinked_skill_entry_is_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            skill = base / "skill"
            skill.mkdir()
            outside = base / "outside.md"
            outside.write_text("---\nname: fake\ndescription: fake\n---\n", encoding="utf-8")
            (skill / "SKILL.md").symlink_to(outside)
            errors = []
            from scripts.packages.validate_skills import check_skill

            errors.extend(check_skill(skill))
            self.assertTrue(any("SKILL.md entrypoint must not be a symlink" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

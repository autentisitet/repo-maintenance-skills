#!/usr/bin/env python3
"""Regression tests for the repository skill validator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_skills import check_openai_yaml, parse_frontmatter


class ValidatorTests(unittest.TestCase):
    def test_invalid_frontmatter_yaml_is_rejected(self) -> None:
        text = "---\nname: demo\ndescription: [unterminated\n---\n# Demo\n"
        with self.assertRaises(ValueError):
            parse_frontmatter(text)

    def test_frontmatter_must_be_mapping(self) -> None:
        with self.assertRaises(ValueError):
            parse_frontmatter("---\n- demo\n---\n# Demo\n")

    def test_frontmatter_rejects_unknown_keys(self) -> None:
        text = "---\nname: demo\ndescription: demo\nunknown: true\n---\n# Demo\n"
        with self.assertRaises(ValueError):
            parse_frontmatter(text)

    def test_invalid_openai_yaml_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "demo"
            config = skill / "agents" / "openai.yaml"
            config.parent.mkdir(parents=True)
            config.write_text("interface: [unterminated\n", encoding="utf-8")
            errors: list[str] = []
            check_openai_yaml(skill, "demo", errors)
            self.assertEqual(len(errors), 1)
            self.assertIn("YAML 无效", errors[0])


if __name__ == "__main__":
    unittest.main()

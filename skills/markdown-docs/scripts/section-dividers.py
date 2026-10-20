#!/usr/bin/env python3
"""Add horizontal rules between level-two Markdown sections."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

H2_RE = re.compile(r"^[ ]{0,3}##(?!#)[ \t]+\S")
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")


def format_markdown(text: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    seen_h2 = False

    for line in lines:
        fence = FENCE_RE.match(line)
        if fence:
            marker, suffix = fence.groups()
            if fence_char is None:
                fence_char = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length and not suffix.strip():
                fence_char = None
                fence_length = 0

        if fence_char is None and H2_RE.match(line):
            if seen_h2:
                while output and not output[-1].strip():
                    output.pop()
                if not output or output[-1].strip() != "---":
                    output.extend(["", "---"])
                output.append("")
            seen_h2 = True
        output.append(line)

    return "\n".join(output) + "\n"


def markdown_files(paths: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".md":
            files.add(path)
        elif path.is_dir():
            for candidate in path.rglob("*.md"):
                if ".git" not in candidate.parts:
                    files.add(candidate)
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    changed: list[Path] = []
    for path in markdown_files(args.paths):
        original = path.read_text(encoding="utf-8")
        formatted = format_markdown(original)
        if formatted == original:
            continue
        changed.append(path)
        if not args.check:
            path.write_text(formatted, encoding="utf-8")

    if args.check and changed:
        for path in changed:
            print(f"缺少二级章节分割线: {path}", file=sys.stderr)
        return 1
    if not args.check:
        print(f"更新 {len(changed)} 个 Markdown 文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

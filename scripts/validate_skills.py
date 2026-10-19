#!/usr/bin/env python3
"""校验 skills/*/SKILL.md 的结构、命名与内部链接。

检查项：
  - SKILL.md 存在，且以 YAML frontmatter 开头
  - name 与目录名一致，符合小写 kebab-case
  - description 非空、不超长、不是占位符
  - Markdown 中引用的相对路径文件存在
  - agents/openai.yaml（若存在）中的 default_prompt 提到 $<name>

退出码 0 表示全部通过。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(\s*([^)\s]+?)\s*\)")
FENCE_RE = re.compile(r"^```.*?^```[ \t]*$", re.DOTALL | re.MULTILINE)
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
PLACEHOLDERS = ("todo", "tbd", "fixme", "xxx", "<description>")
MAX_NAME = 64
MAX_DESC = 1024


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """解析顶层 `key: value` 形式的 frontmatter。"""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return None

    end = normalized.find("\n---\n", 4)
    if end == -1:
        end = normalized.find("\n---", 4)
    if end == -1:
        return None

    data: dict[str, str] = {}
    for line in normalized[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        data[key.strip()] = value
    return data


def strip_code(text: str) -> str:
    """去掉围栏代码块与行内代码，避免把示例链接当成真实链接。"""
    text = FENCE_RE.sub("", text)
    return CODE_SPAN_RE.sub("", text)


def check_links(markdown: Path, errors: list[str]) -> None:
    """确认相对链接指向真实文件。"""
    text = strip_code(markdown.read_text(encoding="utf-8"))
    for raw in LINK_RE.findall(text):
        if raw.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = raw.split("#", 1)[0].split("?", 1)[0]
        if not target:
            continue
        resolved = (markdown.parent / target).resolve()
        if not resolved.exists():
            rel = markdown.relative_to(ROOT)
            errors.append(f"{rel}: 链接目标不存在 -> {raw}")


def check_openai_yaml(skill_dir: Path, name: str, errors: list[str]) -> None:
    cfg = skill_dir / "agents" / "openai.yaml"
    if not cfg.exists():
        return
    text = cfg.read_text(encoding="utf-8")
    prompt = re.search(r"^\s*default_prompt:\s*(.+)$", text, re.MULTILINE)
    if prompt and f"${name}" not in prompt.group(1):
        rel = cfg.relative_to(ROOT)
        errors.append(f"{rel}: default_prompt 应显式提到 ${name}")


def check_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    name = skill_dir.name
    entry = skill_dir / "SKILL.md"
    rel = entry.relative_to(ROOT)

    if not entry.is_file():
        return [f"{skill_dir.relative_to(ROOT)}: 缺少 SKILL.md"]

    text = entry.read_text(encoding="utf-8")
    front = parse_frontmatter(text)
    if front is None:
        return [f"{rel}: 缺少以 --- 包裹的 YAML frontmatter"]

    declared = front.get("name", "")
    if not declared:
        errors.append(f"{rel}: frontmatter 缺少 name")
    elif declared != name:
        errors.append(f"{rel}: name 为 {declared!r}，与目录名 {name!r} 不一致")
    elif not NAME_RE.match(declared):
        errors.append(f"{rel}: name 必须是小写字母、数字和连字符")
    elif len(declared) > MAX_NAME:
        errors.append(f"{rel}: name 超过 {MAX_NAME} 字符")

    desc = front.get("description", "")
    if not desc:
        errors.append(f"{rel}: frontmatter 缺少 description")
    elif len(desc) > MAX_DESC:
        errors.append(f"{rel}: description 超过 {MAX_DESC} 字符（当前 {len(desc)}）")
    else:
        lowered = desc.lower()
        for token in PLACEHOLDERS:
            if token in lowered:
                errors.append(f"{rel}: description 含占位符 {token!r}")

    for markdown in sorted(skill_dir.rglob("*.md")):
        check_links(markdown, errors)

    check_openai_yaml(skill_dir, name, errors)
    return errors


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"找不到 skills 目录: {SKILLS_DIR}", file=sys.stderr)
        return 1

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print("skills 目录为空", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for skill_dir in skill_dirs:
        errors = check_skill(skill_dir)
        status = "FAIL" if errors else "ok  "
        print(f"[{status}] {skill_dir.name}")
        all_errors.extend(errors)

    if all_errors:
        print()
        for error in all_errors:
            print(f"  - {error}")
        print(f"\n{len(all_errors)} 个问题")
        return 1

    print(f"\n{len(skill_dirs)} 个 skill 全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

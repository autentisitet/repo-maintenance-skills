#!/usr/bin/env python3
"""Validate skill packages, Codex metadata and repository resource boundaries.

This is an offline repository checker, not an agent skill loader or execution sandbox.
Compatibility warnings do not block unless --strict is supplied.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
LINK_RE = re.compile(
    r"\]\(\s*(?:<([^>\n]+)>|([^\s)>]+))"
    r"(?:\s+(?:['\"][^\n]*?['\"]|\([^\n)]*\)))?\s*\)"
)
FENCE_RE = re.compile(r"^(`{3,}|~{3,}).*?^\1[ \t]*$", re.DOTALL | re.MULTILINE)
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
PLACEHOLDERS = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b|<description>", re.IGNORECASE)
MAX_NAME, MAX_DESC = 64, 1024
MIN_UI_DESC, MAX_UI_DESC = 25, 64
KNOWN_FRONT_KEYS = {"name", "description", "license", "compatibility", "allowed-tools", "metadata"}
# A heuristic finding requires review; it is not proof of information flow safety.
SENSITIVE_SCRIPT_RE = re.compile(
    r"\bset\s+-x\b|\bprintenv\b|^\s*env\s*$|"
    r"(?:echo|printf|write-host)[^\n]*\$\{?[^}\n]*?(?:token|secret|password|api[_-]?key)\b|"
    r"print\([^\n]*os\.environ",
    re.IGNORECASE | re.MULTILINE,
)
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "uv_cache"}


def display_path(path: Path) -> Path:
    """Return a repository-relative path when possible.

    中文：将诊断路径转换为仓库相对路径；仓库外路径保持原样。
    """
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def yaml_location(exc: yaml.YAMLError) -> str:
    """Report YAML error position without echoing source content.

    中文：只返回行列位置，避免把可能含敏感信息的 YAML 原文写入诊断。
    """
    mark = getattr(exc, "problem_mark", None)
    return f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""


def parse_frontmatter(text: str) -> dict[str, object] | None:
    """Parse YAML frontmatter from the start of a Markdown document.

    中文：仅接受文件开头的字符串键 mapping；缺失 frontmatter 返回 None，非法 YAML 抛错。
    """
    match = FRONTMATTER_RE.match(text.replace("\r\n", "\n"))
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"[Agent Skills] invalid YAML frontmatter{yaml_location(exc)}") from None
    if not isinstance(data, dict) or any(not isinstance(key, str) for key in data):
        raise ValueError("[Agent Skills] YAML frontmatter must be a string-key mapping")
    return data


def strip_code(text: str) -> str:
    """Remove fenced blocks and inline code before prose link scanning.

    中文：移除代码围栏和行内代码，避免把示例中的链接或占位符当作真实资源。
    """
    return CODE_SPAN_RE.sub("", FENCE_RE.sub("", text))


def link_targets(text: str):
    """Yield inline-link targets, including angle-bracket paths with spaces.

    中文：迭代 Markdown 行内链接目标，并支持尖括号包裹的含空格路径。
    """
    for match in LINK_RE.finditer(text):
        yield match.group(1) or match.group(2)


def is_within(path: Path, root: Path) -> bool:
    """Return whether a resolved path remains under the allowed root.

    中文：判断规范化后的资源路径是否仍位于允许的 skill 根目录内。
    """
    return path.is_relative_to(root)


def safe_resource(path: Path, root: Path, errors: list[str]) -> bool:
    """Resolve and contain a resource path before opening it.

    Design/System considerations: Containment is checked after strict resolution, not by string
    prefix, so ``..`` segments and symlink targets cannot escape the package root.
    中文：严格解析资源及父级，拒绝缺失、循环、绝对逃逸和 symlink 越界路径。

    设计/系统考虑：边界判断基于 strict resolve 后的真实路径而非字符串前缀，因此 ``..`` 和 symlink
    目标都无法绕过 skill 根目录限制。
    """
    try:
        resolved = path.resolve(strict=True)
        if not is_within(resolved, root.resolve(strict=True)):
            raise ValueError("path or symlink escapes the skill root")
        return True
    except (OSError, RuntimeError, ValueError):
        errors.append(f"{display_path(path)}: [repository security] path escapes, loops, or is missing; fix the resource path")
        return False


def check_links(markdown: Path, allowed_root: Path, errors: list[str]) -> None:
    """Validate local Markdown links against one allowed resource root.

    中文：忽略外部 URL，检查本地链接是否存在且解析后仍位于 skill 根目录内。
    """
    if not safe_resource(markdown, allowed_root, errors):
        return
    try:
        text = strip_code(markdown.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        errors.append(f"{display_path(markdown)}: [repository] cannot read UTF-8 Markdown")
        return
    for raw in link_targets(text):
        if urlsplit(raw).scheme or raw.startswith(("#", "//")):
            continue
        target = unquote(raw.split("#", 1)[0].split("?", 1)[0])
        if not target:
            continue
        # Normalize Windows separators even when this checker runs on Linux.
        windows = PureWindowsPath(target)
        if Path(target).is_absolute() or windows.drive or windows.root:
            errors.append(f"{display_path(markdown)}: [repository security] resource links must not be absolute")
            continue
        # Parent traversal is allowed only when the resolved target remains in root.
        safe_resource(markdown.parent / target.replace('\\', '/'), allowed_root, errors)


def check_openai_yaml(skill_dir: Path, name: str, errors: list[str]) -> None:
    """Validate optional Codex metadata for one skill package.

    中文：检查 agents/openai.yaml 的 interface、prompt、图标、颜色、policy 和依赖类型。
    """
    cfg = skill_dir / "agents" / "openai.yaml"
    if not cfg.exists() and not cfg.is_symlink():
        return
    if not safe_resource(cfg, skill_dir, errors):
        return
    rel = display_path(cfg)
    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{rel}: [Codex extension] invalid YAML{yaml_location(exc)}")
        return
    except (OSError, UnicodeError):
        errors.append(f"{rel}: [Codex extension] cannot read UTF-8 configuration")
        return
    if not isinstance(data, dict):
        errors.append(f"{rel}: [Codex extension] configuration must be a mapping")
        return
    interface = data.get("interface")
    if not isinstance(interface, dict):
        errors.append(f"{rel}: [repository/Codex] this repository requires an interface mapping")
        return
    for key in ("display_name", "short_description", "default_prompt", "icon_small", "icon_large", "brand_color"):
        if key in interface and not isinstance(interface[key], str):
            errors.append(f"{rel}: [Codex extension] interface.{key} must be a string")
    prompt = interface.get("default_prompt")
    if not isinstance(prompt, str) or not re.search(rf"\${re.escape(name)}(?![a-z0-9-])", prompt):
        errors.append(f"{rel}: [repository/Codex] default_prompt must explicitly reference ${name}")
    short = interface.get("short_description")
    if not isinstance(short, str) or not MIN_UI_DESC <= len(short.strip()) <= MAX_UI_DESC:
        errors.append(f"{rel}: [repository/Codex] short_description must be {MIN_UI_DESC}-{MAX_UI_DESC} characters")
    for key in ("icon_small", "icon_large"):
        icon = interface.get(key)
        if isinstance(icon, str):
            if Path(icon).is_absolute() or PureWindowsPath(icon).drive or PureWindowsPath(icon).root:
                errors.append(f"{rel}: [repository security] {key} must be a relative path inside the skill")
            else:
                safe_resource(skill_dir / icon.replace('\\', '/'), skill_dir, errors)
    if "brand_color" in interface and (
        not isinstance(interface["brand_color"], str)
        or not re.fullmatch(r"#[0-9a-fA-F]{6}", interface["brand_color"])
    ):
        errors.append(f"{rel}: [Codex extension] brand_color must use #RRGGBB")
    policy = data.get("policy", {})
    if not isinstance(policy, dict) or (
        "allow_implicit_invocation" in policy and not isinstance(policy["allow_implicit_invocation"], bool)
    ):
        errors.append(f"{rel}: [Codex extension] policy.allow_implicit_invocation must be boolean")
    dependencies = data.get("dependencies", {})
    if not isinstance(dependencies, dict):
        errors.append(f"{rel}: [Codex extension] dependencies must be a mapping")
    elif "tools" in dependencies:
        tools = dependencies["tools"]
        if not isinstance(tools, list):
            errors.append(f"{rel}: [Codex extension] dependencies.tools must be a list")
        else:
            for tool in tools:
                if not isinstance(tool, dict) or tool.get("type") != "mcp" or not isinstance(tool.get("value"), str):
                    errors.append(f"{rel}: [Codex extension] each tool requires type: mcp and a string value")


def resource_paths(skill_dir: Path):
    """Walk a bounded package tree without following directory symlinks.

    Design/System considerations: Directory symlinks are never followed, and depth/count limits
    bound traversal work against cycles, pathological packages, and denial-of-service inputs.
    中文：限制目录深度和数量遍历 skill 资源，跳过缓存目录且不跟随目录 symlink。

    设计/系统考虑：不跟随目录 symlink，并限制深度与目录数，以约束循环、异常大包和拒绝服务输入。
    """
    queue = [(skill_dir, 0)]
    count = 0
    while queue:
        directory, depth = queue.pop()
        if depth > 6 or count > 2000:
            raise ValueError("[repository] skill resources exceed depth 6 or 2000 directories; reduce package scope")
        count += 1
        for path in sorted(directory.iterdir()):
            if path.is_dir() and not path.is_symlink():
                if path.name not in SKIP_DIRS:
                    queue.append((path, depth + 1))
            else:
                yield path


def check_skill_resources(skill_dir: Path, errors: list[str]) -> None:
    """Check resource containment and obvious sensitive script output.

    中文：验证所有资源边界，并启发式检查脚本是否可能输出环境或凭据。
    """
    try:
        for path in resource_paths(skill_dir):
            if not safe_resource(path, skill_dir, errors):
                continue
            if not path.is_file() or "scripts" not in path.relative_to(skill_dir).parts:
                continue
            if path.suffix not in {".sh", ".py", ".ps1", ".js", ".mjs"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                errors.append(f"{display_path(path)}: [repository] cannot read UTF-8 script")
                continue
            if SENSITIVE_SCRIPT_RE.search(text):
                errors.append(f"{display_path(path)}: [repository security] possible environment or credential output; review and remove it")
    except (OSError, ValueError) as exc:
        errors.append(f"{display_path(skill_dir)}: {exc}")


def check_authoring_structure(skill_dir: Path, warnings: list[str], errors: list[str]) -> None:
    """Check progressive disclosure and resource discoverability policy.

    中文：检查正文长度、reference 入口、目录提示、script 可发现性、shebang 和执行位。
    """
    entry = skill_dir / "SKILL.md"
    try:
        text = entry.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return
    match = FRONTMATTER_RE.match(text.replace("\r\n", "\n"))
    body = text[match.end():] if match else text
    if len(body.splitlines()) > 500:
        warnings.append(f"{display_path(entry)}: [repository authoring] body exceeds 500 lines; use progressive disclosure")

    linked_references: set[str] = set()
    for raw in link_targets(strip_code(body)):
        target = unquote(raw.split("#", 1)[0].split("?", 1)[0]).replace("\\", "/")
        if target.startswith("references/"):
            linked_references.add(Path(target).as_posix())

    references = skill_dir / "references"
    if references.is_dir():
        for path in sorted(references.rglob("*.md")):
            relative = path.relative_to(skill_dir).as_posix()
            if relative not in linked_references:
                warnings.append(f"{display_path(path)}: [repository authoring] reference is not linked directly from SKILL.md")
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError):
                continue
            headings = {line.strip().casefold() for line in lines[:40]}
            if len(lines) > 100 and not headings.intersection({"## contents", "## table of contents"}):
                warnings.append(f"{display_path(path)}: [repository authoring] exceeds 100 lines; add a short contents section near the top")

    scripts = skill_dir / "scripts"
    if not scripts.is_dir():
        return
    for path in sorted(
        item
        for item in scripts.rglob("*")
        if item.is_file() and not any(part in SKIP_DIRS for part in item.relative_to(scripts).parts)
    ):
        relative = path.relative_to(skill_dir).as_posix()
        if relative not in body:
            warnings.append(f"{display_path(path)}: [repository authoring] script is not listed in SKILL.md")
        if path.suffix in {".py", ".sh"}:
            try:
                first_line = path.read_text(encoding="utf-8").splitlines()[:1]
            except (OSError, UnicodeError):
                continue
            if not first_line or not first_line[0].startswith("#!"):
                warnings.append(f"{display_path(path)}: [repository authoring] executable script is missing a shebang")
            if os.name != "nt" and not os.access(path, os.X_OK):
                errors.append(f"{display_path(path)}: [repository] script lacks the POSIX executable bit")


def check_skill(skill_dir: Path, warnings: list[str] | None = None) -> list[str]:
    """Validate one complete skill package and return blocking errors.

    中文：组合 frontmatter、资源、安全、authoring 和 Codex metadata 检查；warning 由调用方传入收集。
    """
    errors: list[str] = []
    warnings = warnings if warnings is not None else []
    name = skill_dir.name
    entry = skill_dir / "SKILL.md"
    rel = display_path(entry)
    if skill_dir.is_symlink():
        return [f"{rel}: [repository security] skill root must not be a symlink"]
    if entry.is_symlink():
        return [f"{rel}: [repository security] SKILL.md entrypoint must not be a symlink"]
    if not safe_resource(entry, skill_dir, errors):
        return errors
    try:
        front = parse_frontmatter(entry.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError) as exc:
        return [f"{rel}: {exc}"]
    if front is None:
        return [f"{rel}: [Agent Skills] missing YAML frontmatter delimited by ---"]
    if set(front) - KNOWN_FRONT_KEYS:
        warnings.append(f"{rel}: [compatibility] unknown frontmatter field; verify target-client support")
    declared = front.get("name")
    if not isinstance(declared, str) or not declared.strip():
        errors.append(f"{rel}: [Agent Skills] name must be a non-empty string")
    else:
        if declared != name:
            warnings.append(f"{rel}: [Agent Skills] name does not match the directory")
        if not NAME_RE.fullmatch(declared):
            errors.append(f"{rel}: [Agent Skills] name must be lowercase kebab-case")
        if len(declared) > MAX_NAME:
            warnings.append(f"{rel}: [Agent Skills] name exceeds {MAX_NAME} characters")
    desc = front.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append(f"{rel}: [Agent Skills] description must be a non-empty string")
    elif len(desc) > MAX_DESC:
        errors.append(f"{rel}: [Agent Skills] description exceeds {MAX_DESC} characters")
    elif PLACEHOLDERS.search(desc):
        errors.append(f"{rel}: [repository] description contains a placeholder")
    for key in ("license", "compatibility", "allowed-tools"):
        if key in front and not isinstance(front[key], str):
            errors.append(f"{rel}: [Agent Skills] {key} must be a string")
    if isinstance(front.get("compatibility"), str) and len(front["compatibility"]) > 500:
        errors.append(f"{rel}: [Agent Skills] compatibility exceeds 500 characters")
    if "metadata" in front:
        metadata = front["metadata"]
        if not isinstance(metadata, dict) or any(
            not isinstance(key, str) or not isinstance(value, str) for key, value in metadata.items()
        ):
            errors.append(f"{rel}: [Agent Skills] metadata must be a string-to-string mapping")
    check_skill_resources(skill_dir, errors)
    check_authoring_structure(skill_dir, warnings, errors)
    try:
        for markdown in resource_paths(skill_dir):
            if markdown.suffix == ".md":
                check_links(markdown, skill_dir, errors)
    except (OSError, ValueError) as exc:
        errors.append(f"{rel}: {exc}")
    check_openai_yaml(skill_dir, declared if isinstance(declared, str) else name, errors)
    return errors


def main() -> int:
    """Validate all repository skills and print errors or warnings.

    中文：解析 strict/json 参数，扫描 skills 目录，并按策略决定 warning 是否导致非零退出。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="write structured diagnostics as JSON")
    parser.add_argument("--strict", action="store_true", help="treat compatibility warnings as failures")
    args = parser.parse_args()
    if not SKILLS_DIR.is_dir():
        print("[repository] skills directory not found", file=sys.stderr)
        return 1
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    errors: list[str] = []
    warnings: list[str] = []
    if not skill_dirs:
        errors.append("[repository] skills directory is empty")
    for skill in skill_dirs:
        errors.extend(check_skill(skill, warnings))
    for markdown in sorted(ROOT.glob("*.md")):
        check_links(markdown, ROOT, errors)
    ok = not errors and not (args.strict and warnings)
    summary = {"ok": ok, "skills": len(skill_dirs), "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for item in errors:
            print(f"error: {item}", file=sys.stderr)
        for item in warnings:
            print(f"warning: {item}", file=sys.stderr)
        print(f"Validated {len(skill_dirs)} skills: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

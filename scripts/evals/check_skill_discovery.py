#!/usr/bin/env python3
"""Check actual Codex app-server skill discovery without a model call."""

from __future__ import annotations

import argparse
import json
import os
import selectors
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAFE_ENV = {"HOME", "PATH", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP"}


def link_project_skills(workspace: Path, skills_dir: Path) -> None:
    """Expose repository skills inside a temporary workspace.

    Design/System considerations: POSIX directory symlinks and Windows junctions are the closest
    portable equivalents, but junction creation requires a native ``cmd /c mklink /J`` subprocess.
    中文：在临时 workspace 的 `.agents/skills` 中创建 symlink 或 Windows junction。

    设计/系统考虑：POSIX 使用目录 symlink，Windows 使用 junction；后者必须通过原生
    ``cmd /c mklink /J`` 创建，失败输出不回显以避免泄露主机信息。
    """
    destination = workspace / ".agents" / "skills"
    destination.mkdir(parents=True)
    for source in sorted(skills_dir.iterdir()):
        if not (source / "SKILL.md").is_file():
            continue
        target = destination / source.name
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(target), str(source)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise OSError("cannot create a temporary skill junction; raw output omitted")
        else:
            target.symlink_to(source, target_is_directory=True)


def check(workspace: Path, timeout: int = 30) -> dict[str, object]:
    """Query Codex app-server and verify repository-scope skill discovery.

    Design/System considerations: The app-server speaks newline-delimited JSON-RPC over pipes.
    A selector enforces one absolute timeout while unrelated notifications are ignored, and the
    child is always terminated or killed during cleanup.
    中文：使用隔离 CODEX_HOME 调用 app-server，校验 skill 数量、来源、scope 和启用状态。

    设计/系统考虑：app-server 通过 pipe 传输逐行 JSON-RPC；selector 在单一 deadline 下过滤
    无关通知，finally 中必须回收子进程，避免 CI 悬挂。
    """
    if not shutil.which("codex"):
        raise RuntimeError("codex CLI not found")
    codex_home = workspace / ".codex-home"
    codex_home.mkdir()
    environment = {
        key: value for key, value in os.environ.items() if key in SAFE_ENV
    }
    environment["CODEX_HOME"] = str(codex_home)
    process = subprocess.Popen(
        ["codex", "app-server", "--stdio"],
        cwd=workspace,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    if process.stdin is None or process.stdout is None:
        process.kill()
        raise RuntimeError("cannot connect to Codex app-server stdio")
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)

    def send(value: dict[str, object]) -> None:
        """Send one JSON-RPC message to the app-server process.

        Design/System considerations: Each request is one JSON line and must be flushed because
        the peer is waiting on a pipe rather than a terminal.
        中文：向 app-server 标准输入写入并刷新一条 JSON-RPC 消息。

        设计/系统考虑：每个请求必须编码成单行 JSON 并立即 flush，否则 pipe 对端可能持续等待。
        """
        process.stdin.write(json.dumps(value) + "\n")
        process.stdin.flush()

    def receive(identifier: int) -> dict[str, object]:
        """Wait for one matching JSON-RPC response within the timeout.

        Design/System considerations: JSON-RPC notifications and malformed noise may precede the
        response, so only the matching id completes the call; the remaining timeout is recalculated
        on every wait to prevent timeout extension.
        中文：在超时前读取指定 id 的响应；协议错误和超时会转换为受控异常。

        设计/系统考虑：响应前可能混有通知或非法行，因此只接受匹配 id；每次等待都用剩余时间，
        防止循环意外延长总超时。
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not selector.select(timeout=max(0, deadline - time.monotonic())):
                break
            line = process.stdout.readline()
            if not line:
                break
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(value, dict) or value.get("id") != identifier:
                continue
            if "error" in value or not isinstance(value.get("result"), dict):
                raise RuntimeError("Codex app-server rejected the request or returned an invalid response; raw output omitted")
            return value["result"]
        raise RuntimeError("Codex app-server timed out or exited; raw output omitted")

    try:
        send({
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "repo-maintenance-skill-eval", "version": "1.0"}},
        })
        receive(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "skills/list", "params": {"cwds": [str(workspace)], "forceReload": True}})
        response = receive(2)
        expected = {
            path.name: (path / "SKILL.md").resolve()
            for path in (ROOT / "skills").iterdir()
            if (path / "SKILL.md").is_file()
        }
        data = response.get("data")
        if not isinstance(data, list):
            raise RuntimeError("Codex app-server returned invalid skill data; raw output omitted")
        found: dict[str, dict[str, object]] = {}
        duplicates: set[str] = set()
        discovery_errors = 0
        for group in data:
            if not isinstance(group, dict):
                continue
            errors = group.get("errors", [])
            if isinstance(errors, list):
                discovery_errors += len(errors)
            skills = group.get("skills", [])
            if not isinstance(skills, list):
                continue
            for skill in skills:
                if not isinstance(skill, dict):
                    continue
                name, path = skill.get("name"), skill.get("path")
                if name not in expected or not isinstance(path, str):
                    continue
                if name in found:
                    duplicates.add(name)
                    continue
                found[name] = {
                    "name": name,
                    "enabled": skill.get("enabled"),
                    "scope": skill.get("scope"),
                    "source_matches": Path(path).resolve() == expected[name],
                }
        complete = discovery_errors == 0 and not duplicates and all(
            name in found
            and found[name]["enabled"] is True
            and found[name]["scope"] == "repo"
            and found[name]["source_matches"] is True
            for name in expected
        )
        return {
            "expected": len(expected),
            "found": [found[name] for name in sorted(found)],
            "duplicate_names": sorted(duplicates),
            "discovery_errors": discovery_errors,
            "complete": complete,
        }
    finally:
        selector.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdin.close()
        process.stdout.close()


def main() -> int:
    """Run isolated discovery and optionally write its JSON report.

    中文：创建临时 workspace，执行 discovery 校验，并按需原子写入结果文件。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("--timeout must be greater than zero")
    with tempfile.TemporaryDirectory(prefix="skill-discovery-") as directory:
        workspace = Path(directory)
        link_project_skills(workspace, ROOT / "skills")
        result = check(workspace, args.timeout)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(args.output)
    print(text, end="")
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

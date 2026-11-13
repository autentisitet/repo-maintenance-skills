#!/usr/bin/env python3
"""Observe skill entrypoint reads in fresh Codex sessions."""

from __future__ import annotations

import argparse
import codecs
import concurrent.futures
import hashlib
import json
import os
import re
import selectors
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from scripts.evals.check_skill_discovery import link_project_skills

ROOT = Path(__file__).resolve().parents[2]
FRONTMATTER_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
TRANSIENT_FAILURES = {"timeout", "completion_event_missing"}
# Cap tool output retained per command in each fresh Codex session. The eval only
# needs the entrypoint header (skill name + first heading), which always sits at
# the top of SKILL.md, so a modest cap keeps context and JSONL output small
# without losing routing evidence.
DEFAULT_TOOL_OUTPUT_TOKEN_LIMIT = 8000


def load_cases(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    """Load minimally valid activation cases from one dataset file.

    中文：读取 query 数组并检查 runner 必需字段；错误以字符串列表返回而非直接抛出。
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [], [f"{path}: cannot read eval dataset: {exc}"]
    queries = data.get("queries") if isinstance(data, dict) else None
    if not isinstance(queries, list):
        return [], [f"{path}: top-level object must contain a queries array"]
    errors: list[str] = []
    cases: list[dict[str, object]] = []
    for index, case in enumerate(queries):
        location = f"{path}:queries[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{location}: case must be an object")
            continue
        required = ("id", "skill", "query", "should_trigger")
        if not all(key in case for key in required):
            errors.append(f"{location}: missing required fields")
            continue
        if not all(isinstance(case[key], str) and case[key].strip() for key in ("id", "skill", "query")):
            errors.append(f"{location}: id, skill, and query must be non-empty strings")
            continue
        if not isinstance(case["should_trigger"], bool):
            errors.append(f"{location}: should_trigger must be boolean")
            continue
        cases.append(case)
    return cases, errors


def skill_markers(entry: Path) -> tuple[str, str]:
    """Extract stable frontmatter and heading markers from one skill entrypoint.

    中文：读取 SKILL.md 的 name 标记和一级标题，用于判定真实入口读取证据。
    """
    try:
        text = entry.read_text(encoding="utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"cannot read skill entrypoint: {entry}") from exc
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise RuntimeError(f"malformed skill frontmatter: {entry}")
    name_marker = f"name: {entry.parent.name}"
    heading = next((line for line in text[match.end():].splitlines() if line.startswith("# ")), "")
    if not heading:
        raise RuntimeError(f"missing skill heading: {entry}")
    return name_marker, heading


def load_skill_markers() -> list[tuple[str, str, str]]:
    """Compute every skill's entrypoint markers once per runner invocation.

    中文：一次性缓存全部 skill 的入口标记，避免每条 trial 重复读取文件。
    """
    markers = []
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        entry = skill_dir / "SKILL.md"
        if entry.is_file():
            markers.append((skill_dir.name, *skill_markers(entry)))
    return markers


def match_line(
    line: str,
    markers: list[tuple[str, str, str]],
    observed: set[str],
    state: dict[str, object],
) -> None:
    """Fold one JSONL event into the running observation state.

    Skill activation is judged only from explicit tool-call evidence: a
    successful ``command_execution`` whose command reads ``SKILL.md`` and whose
    aggregated output contains the entrypoint markers. Self-reports and partial
    output never count, so a positive observation is deterministic.

    Design/System considerations: JSONL is treated as an append-only event stream. Only a
    successful ``command_execution`` containing both stable entrypoint markers becomes routing
    evidence; agent prose, failed commands, and partial output cannot mutate the observed set.
    中文：解析单条 Codex JSONL 事件，累计 usage 和 SKILL.md 入口标记证据。

    设计/系统考虑：JSONL 被视为只追加事件流；只有成功命令且同时包含稳定入口标记才归约为路由
    证据，自述、失败命令和截断输出都不能改变 observed 状态。
    """
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return
    if not isinstance(event, dict):
        return
    event_type = event.get("type")
    if event_type == "turn.completed":
        state["turn_completed"] = True
        raw_usage = event.get("usage")
        if isinstance(raw_usage, dict):
            state["usage"] = {
                key: value
                for key, value in raw_usage.items()
                if key in {"input_tokens", "cached_input_tokens", "output_tokens"}
                and type(value) is int
            }
    item = event.get("item")
    if event_type != "item.completed" or not isinstance(item, dict):
        return
    if item.get("type") != "command_execution" or item.get("exit_code") != 0:
        return
    command = item.get("command", "")
    output = item.get("aggregated_output", "")
    if not isinstance(command, str) or not isinstance(output, str):
        return
    output = output.replace("\r\n", "\n")
    for name, name_marker, heading_marker in markers:
        if (
            "SKILL.md" in command
            and (name in command or name_marker in output)
            and name_marker in output
            and heading_marker in output
        ):
            observed.add(name)


def observe(
    jsonl_output: str,
    markers: list[tuple[str, str, str]] | None = None,
) -> dict[str, object]:
    """Observe complete JSONL output as a non-streaming fallback.

    中文：逐行折叠完整 JSONL 文本，供测试和非流式场景提取入口读取与 usage。
    """
    if markers is None:
        markers = load_skill_markers()
    observed: set[str] = set()
    state: dict[str, object] = {"turn_completed": False, "usage": {}}
    for line in jsonl_output.splitlines():
        match_line(line, markers, observed, state)
    return {
        "observed_reads": sorted(observed),
        "turn_completed": state["turn_completed"],
        "usage": state["usage"],
    }


def sample_cases(cases: list[dict[str, object]], per_label: int | None) -> list[dict[str, object]]:
    """Select deterministic positive and negative samples per skill.

    中文：按 skill 和标签稳定排序采样；None 表示保留全部 case。
    """
    if per_label is None:
        return cases
    grouped: dict[tuple[str, bool], list[dict[str, object]]] = {}
    for case in cases:
        key = (str(case["skill"]), bool(case["should_trigger"]))
        grouped.setdefault(key, []).append(case)
    sampled: list[dict[str, object]] = []
    for key in sorted(grouped):
        sampled.extend(sorted(grouped[key], key=lambda item: str(item["id"]))[:per_label])
    return sorted(sampled, key=lambda item: (str(item["skill"]), str(item["id"])))


def query_sha256(case: dict[str, object]) -> str:
    """Hash the case fields that affect one activation decision.

    中文：规范化并哈希 id、skill、category、query 和标签，用于安全复用旧 trial。
    """
    canonical = {
        key: case.get(key)
        for key in ("id", "skill", "category", "query", "should_trigger")
    }
    return hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def trial_is_decided(trial: dict[str, object]) -> bool:
    """Return whether a trial contains a reliable pass or fail decision.

    中文：仅把非基础设施故障的 pass/fail 视为可复用的确定结果。
    """
    return (
        trial.get("status") in {"pass", "fail"}
        and not trial.get("infrastructure_failure")
    )


def outcome_status(loaded: bool, expected: bool) -> str:
    """Return pass or fail for reliable routing evidence.

    中文：比较实际读取与期望标签，将可靠结果统一映射为 pass 或 fail。
    """
    return "pass" if loaded == expected else "fail"


def terminate_process(process: subprocess.Popen) -> None:
    """Terminate a child process and escalate to kill after five seconds.

    Design/System considerations: Termination is cooperative first and forceful second. Waiting
    after both signals is required to reap the process and avoid zombies or lingering CI workers.
    中文：先发送 terminate，超时后 kill，并等待子进程回收以避免残留进程。

    设计/系统考虑：先协作式 terminate，再强制 kill；两条路径都必须 wait 回收，避免僵尸进程或
    CI 残留 worker。
    """
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def wait_process_until(process: subprocess.Popen, deadline: float) -> int | None:
    """Wait until the case deadline and terminate the child on expiry.

    Design/System considerations: An absolute monotonic deadline prevents repeated waits from
    extending the budget and is immune to wall-clock changes.
    中文：按绝对 deadline 等待子进程；超时会终止进程并返回 None。

    设计/系统考虑：使用 monotonic 绝对 deadline，既避免多次 wait 延长预算，也不受系统时钟跳变影响。
    """
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        terminate_process(process)
        return None
    try:
        return process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        terminate_process(process)
        return None


def run_case(
    case: dict[str, object],
    timeout: int,
    markers: list[tuple[str, str, str]] | None = None,
    tool_output_token_limit: int = DEFAULT_TOOL_OUTPUT_TOKEN_LIMIT,
    early_stop: bool = True,
    model: str | None = None,
) -> dict[str, object]:
    """Run one fresh Codex session and stream its JSONL events.

    As soon as the target skill's entrypoint read is observed in a tool call, the
    outcome is fixed (positive -> pass, negative -> fail) and the process is
    terminated early so the next sample can start. Negative samples that never
    read the target skill still run to completion to prove the absence.

    Design/System considerations: Each query gets a fresh workspace and read-only Codex sandbox.
    Multi-agent and bundled skills are disabled to control routing; stderr/raw model output are
    not persisted. Read available pipe bytes instead of blocking on a newline after select, so
    a partial JSONL event cannot extend the monotonic deadline.
    中文：在临时只读 workspace 中执行单条 query，支持早停、超时和受控基础设施失败分类。

    设计/系统考虑：每条 query 使用全新 workspace 和只读 sandbox；关闭多代理与 bundled skills；
    不持久化 stderr/原始模型输出，仅在入口标记证据出现后早停。
    """
    started = time.monotonic()
    target = str(case["skill"])
    expected = bool(case["should_trigger"])
    if markers is None:
        markers = load_skill_markers()
    try:
        with tempfile.TemporaryDirectory(prefix="skill-activation-") as directory:
            workspace = Path(directory)
            link_project_skills(workspace, ROOT / "skills")
            command = [
                "codex", "exec", "--ephemeral", "--json", "--skip-git-repo-check",
                "--disable", "multi_agent",
                "--sandbox", "read-only",
                "-c", 'shell_environment_policy.inherit="core"',
                "-c", f"tool_output_token_limit={tool_output_token_limit}",
                "-c", "skills.bundled.enabled=false",
            ]
            if model:
                command += ["-m", model]
            command.append("-")
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                cwd=workspace,
                text=True,
                bufsize=1,
            )
            if process.stdin is not None:
                try:
                    process.stdin.write(str(case["query"]))
                except OSError:
                    pass
                finally:
                    process.stdin.close()

            observed: set[str] = set()
            state: dict[str, object] = {"turn_completed": False, "usage": {}}

            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            deadline = started + timeout
            timed_out = False
            early_stopped = False
            decoder = codecs.getincrementaldecoder("utf-8")()
            pending_line = ""
            try:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        timed_out = True
                        break
                    if not selector.select(timeout=remaining):
                        continue
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        pending_line += decoder.decode(b"", final=True)
                        if pending_line:
                            match_line(pending_line, markers, observed, state)
                        break
                    pending_line += decoder.decode(chunk)
                    while "\n" in pending_line:
                        line, pending_line = pending_line.split("\n", 1)
                        match_line(line, markers, observed, state)
                        if early_stop and target in observed:
                            early_stopped = True
                            break
                    if early_stopped:
                        break
            finally:
                selector.close()

            if timed_out:
                terminate_process(process)
                process.stdout.close()
                return {
                    "status": "inconclusive",
                    "infrastructure_failure": True,
                    "reason": "timeout",
                    "duration_seconds": round(time.monotonic() - started, 3),
                }

            if early_stopped:
                terminate_process(process)
                process.stdout.close()
                loaded = True
                status = outcome_status(loaded, expected)
                return {
                    "status": status,
                    "observed_skill_read": loaded,
                    "observed_reads": sorted(observed),
                    "usage": state["usage"],
                    "early_stopped": True,
                    "duration_seconds": round(time.monotonic() - started, 3),
                }

            returncode = wait_process_until(process, deadline)
            process.stdout.close()
            if returncode is None:
                return {
                    "status": "inconclusive",
                    "infrastructure_failure": True,
                    "reason": "timeout",
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            if returncode != 0:
                return {
                    "status": "inconclusive",
                    "infrastructure_failure": True,
                    "reason": "agent_process_failed",
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            if not state["turn_completed"]:
                return {
                    "status": "inconclusive",
                    "infrastructure_failure": True,
                    "reason": "completion_event_missing",
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            loaded = target in observed
            status = outcome_status(loaded, expected)
            return {
                "status": status,
                "observed_skill_read": loaded,
                "observed_reads": sorted(observed),
                "usage": state["usage"],
                "duration_seconds": round(time.monotonic() - started, 3),
            }
    except (OSError, RuntimeError, UnicodeError, ValueError):
        return {
            "status": "inconclusive",
            "infrastructure_failure": True,
            "reason": "evaluation_unavailable",
            "duration_seconds": round(time.monotonic() - started, 3),
        }


def run_preflight(
    case: dict[str, object],
    timeout: int,
    markers: list[tuple[str, str, str]] | None = None,
    tool_output_token_limit: int = DEFAULT_TOOL_OUTPUT_TOKEN_LIMIT,
    early_stop: bool = True,
    model: str | None = None,
) -> dict[str, object]:
    """Run the first case and retry transient failures once.

    中文：执行基础设施预检；timeout 或 completion 缺失时额外增加 60 秒重试一次。
    """
    result = run_case(case, timeout, markers, tool_output_token_limit, early_stop, model)
    if result.get("infrastructure_failure") and result.get("reason") in TRANSIENT_FAILURES:
        result = run_case(case, timeout + 60, markers, tool_output_token_limit, early_stop, model)
    return result


def skills_digest() -> str:
    """Hash every tracked skill resource that affects evaluation behavior.

    Design/System considerations: Paths and bytes are both hashed in sorted order so renames and
    content edits invalidate reuse, while generated bytecode and cache directories stay irrelevant.
    中文：按稳定路径顺序哈希 skill 文件内容，忽略缓存文件，用于结果 freshness 和复用门。

    设计/系统考虑：按稳定顺序同时哈希相对路径与文件字节，使重命名和内容修改都会失效；缓存与
    bytecode 不参与结果身份。
    """
    digest = hashlib.sha256()
    for path in sorted((ROOT / "skills").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def runner_digest() -> str:
    """Hash the evaluator and discovery helper used to observe skill reads.

    中文：哈希评测脚本及其技能发现辅助脚本；执行逻辑变化时禁止复用旧 trial。
    """
    digest = hashlib.sha256()
    source_root = Path(__file__).resolve().parents[2]
    for path in (Path(__file__).resolve(), source_root / "scripts/evals/check_skill_discovery.py"):
        digest.update(path.relative_to(source_root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def detect_codex_version() -> str | None:
    """Return the actual Codex CLI version used for this evaluation.

    中文：调用 `codex --version`；不可用、超时或非零退出时返回 None。
    """
    try:
        completed = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return next((line.strip() for line in completed.stdout.splitlines() if line.strip()), None)


def previous_reuse_map(
    output: Path,
    model: str | None,
    runner_sha: str,
    codex_version: str | None,
    skills_sha: str,
    cases: list[dict[str, object]],
    runs: int,
) -> dict[int, list[dict[str, object]]]:
    """Return compatible previously decided trials indexed by case position.

    Reuse requires the pinned model, runner digest, actual Codex version, and
    skill package digest to match. Per-case reuse additionally requires the
    same ``query_sha256`` and a full set of decided trials.

    Design/System considerations: Reuse is fail-closed. Missing Codex version or runner digest,
    changed skill bytes, changed query semantics, incomplete trials, or infrastructure failures all
    force fresh model calls rather than mixing incomparable evidence.
    中文：只有 runner、Codex 版本、模型、skill 摘要、query 摘要和 trial 数全部一致时才复用。

    设计/系统考虑：复用采用 fail-closed；缺少 Codex 版本或 runner 摘要、skill/query 变化、trial 不完整
    或基础设施失败都会强制重跑，避免混合不可比较证据。
    """
    if model is None or codex_version is None:
        return {}
    try:
        previous = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(previous, dict):
        return {}
    if previous.get("evaluation_kind") != "observed_entrypoint_reads":
        return {}
    if previous.get("runner_sha256") != runner_sha:
        return {}
    if previous.get("codex_version") != codex_version:
        return {}
    if previous.get("model") != model:
        return {}
    if previous.get("skills_sha256") != skills_sha:
        return {}
    previous_rows = {
        row.get("id"): row
        for row in previous.get("results", [])
        if isinstance(row, dict)
    }
    reuse: dict[int, list[dict[str, object]]] = {}
    for index, case in enumerate(cases):
        row = previous_rows.get(case.get("id"))
        if not isinstance(row, dict):
            continue
        if row.get("query_sha256") != query_sha256(case):
            continue
        trials = row.get("trials")
        if not isinstance(trials, list) or len(trials) != runs:
            continue
        if any(not trial_is_decided(trial) for trial in trials):
            continue
        reuse[index] = [dict(trial) for trial in trials]
    return reuse


def main() -> int:
    """Run model-backed activation evaluations and save incremental results.

    中文：解析 runner 参数，执行预检和并发 trial，并在每次完成后原子更新结果 JSON。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--allow-model-calls", action="store_true")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--model",
        help="pin the model served to each session and gate result reuse on it",
    )
    parser.add_argument("--sample-per-label", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.allow_model_calls:
        parser.error("explicit --allow-model-calls is required")
    if args.runs < 1 or not 1 <= args.jobs <= 4 or args.timeout < 1:
        parser.error("--runs and --timeout must be positive; --jobs must be 1..4")
    if args.sample_per_label is not None and args.sample_per_label < 1:
        parser.error("--sample-per-label must be positive")

    cases, errors = load_cases(args.dataset)
    if errors or not cases:
        parser.error("invalid or empty dataset: " + "; ".join(errors))
    known_skills = {path.name for path in (ROOT / "skills").iterdir() if (path / "SKILL.md").is_file()}
    if any(str(case["skill"]) not in known_skills for case in cases):
        parser.error("dataset references an unknown skill")
    cases = sample_cases(cases, args.sample_per_label)
    markers = load_skill_markers()
    skills_sha = skills_digest()
    runner_sha = runner_digest()
    codex_version = detect_codex_version()
    rows = [
        {
            "id": case["id"],
            "skill": case["skill"],
            "category": case.get("category"),
            "should_trigger": case["should_trigger"],
            "query_sha256": query_sha256(case),
            "trials": [],
        }
        for case in cases
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save() -> dict[str, object]:
        """Atomically persist current progress and return the result payload.

        中文：重新计算进度计数，将当前 rows 写入临时文件后原子替换输出文件。
        """
        trials = [trial for row in rows for trial in row["trials"]]
        payload: dict[str, object] = {
            "evaluation_kind": "observed_entrypoint_reads",
            "runner_sha256": runner_sha,
            "codex_version": codex_version,
            "model": args.model,
            "skills_sha256": skills_sha,
            "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
            "sample_per_label": args.sample_per_label,
            "completed_trials": len(trials),
            "expected_trials": len(cases) * args.runs,
            "passes": sum(trial["status"] == "pass" for trial in trials),
            "failures": sum(trial["status"] == "fail" for trial in trials),
            "inconclusive": sum(trial["status"] == "inconclusive" for trial in trials),
            "results": rows,
        }
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.output)
        return payload

    reuse = previous_reuse_map(
        args.output,
        args.model,
        runner_sha,
        codex_version,
        skills_sha,
        cases,
        args.runs,
    )
    pending_indices: list[int] = []
    for index in range(len(cases)):
        if index in reuse:
            rows[index]["trials"] = reuse[index]
            rows[index]["reused"] = True
        else:
            pending_indices.append(index)

    print(
        f"{len(reuse)}/{len(cases)} cases reused from {args.output.name}; "
        f"{len(pending_indices)} case(s) to run",
        file=sys.stderr,
    )
    if pending_indices:
        first_index = pending_indices[0]
        preflight = run_preflight(
            cases[first_index],
            args.timeout,
            markers,
            DEFAULT_TOOL_OUTPUT_TOKEN_LIMIT,
            True,
            args.model,
        )
        rows[first_index]["trials"].append(preflight)
        if preflight.get("infrastructure_failure"):
            existing_output = args.output.exists()
            if not existing_output:
                save()
            print(
                f"preflight failed: {preflight.get('reason', 'unknown')}; "
                "remaining model calls were not started; "
                + ("existing output preserved" if existing_output else "failure saved"),
                file=sys.stderr,
            )
            return 2
    payload = save()

    tasks: list[tuple[int, dict[str, object]]] = []
    for index in pending_indices:
        remaining = args.runs - 1 if index == pending_indices[0] else args.runs
        tasks.extend((index, cases[index]) for _ in range(remaining))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {
            pool.submit(
                run_case,
                case,
                args.timeout,
                markers,
                DEFAULT_TOOL_OUTPUT_TOKEN_LIMIT,
                True,
                args.model,
            ): index
            for index, case in tasks
        }
        for future in concurrent.futures.as_completed(pending):
            rows[pending[future]]["trials"].append(future.result())
            payload = save()
            print(
                f"{payload['completed_trials']}/{payload['expected_trials']} trials; "
                f"{payload['passes']} pass, {payload['failures']} fail, "
                f"{payload['inconclusive']} inconclusive",
                file=sys.stderr,
                flush=True,
            )
    return 0 if payload["passes"] == payload["expected_trials"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

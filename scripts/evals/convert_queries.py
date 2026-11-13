#!/usr/bin/env python3
"""Convert routing query sets between JSON and CSV, and check the two stay in sync.

The JSON form is the source of truth for the runner; the CSV form exists so a
human can review or bulk-edit the datasets in Excel. CSV is written with a UTF-8
BOM so Excel opens the Chinese query text correctly, and every field is quoted
by the standard ``csv`` module when it needs to be.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

CSV_FIELDS = ("id", "skill", "category", "query", "should_trigger")
SPLITS = {"train", "validation"}
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def escape_excel_cell(value: str) -> str:
    """Prevent Excel from evaluating query-set text as a formula.

    Design/System considerations: CSV quoting does not stop spreadsheet formula execution;
    prefixing an apostrophe is the interoperable text escape used by Excel-like applications.
    中文：对公式前缀和前导单引号加转义，确保 CSV 在 Excel 中按文本打开。

    设计/系统考虑：CSV 引号不能阻止电子表格执行公式；前置单引号用于把危险前缀强制解释为文本。
    """
    if value.startswith("'") or value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def unescape_excel_cell(value: str) -> str:
    """Reverse only escapes emitted by :func:`escape_excel_cell`.

    Design/System considerations: Unescaping is deliberately asymmetric and pattern-limited so an
    ordinary leading apostrophe is not silently removed from user data.
    中文：仅撤销本导出器添加的单引号，不改动用户原有的普通文本。

    设计/系统考虑：反转义只识别本导出器可生成的模式，避免误删用户原有的前导单引号。
    """
    if value.startswith("''") or (
        value.startswith("'") and value[1:].startswith(FORMULA_PREFIXES)
    ):
        return value[1:]
    return value


def infer_split(path: Path) -> str | None:
    """Infer the dataset split from a conventional filename.

    中文：从文件名识别 train 或 validation；无法判断时返回 None。
    """
    name = path.stem.casefold()
    if "validation" in name or "val" in name:
        return "validation"
    if "train" in name:
        return "train"
    return None


def parse_bool(raw: str) -> bool:
    """Parse the supported CSV boolean spellings.

    中文：只接受 true/false 或 1/0，其他值抛出 ValueError。
    """
    value = raw.strip().casefold()
    if value in {"true", "1"}:
        return True
    if value in {"false", "0"}:
        return False
    raise ValueError(f"should_trigger must be true/false (or 1/0), got {raw!r}")


def load_json(path: Path) -> dict[str, object]:
    """Read and validate a JSON query-set payload, returning it unchanged.

    中文：读取 canonical JSON，并检查 split 和 queries 顶层结构，不重写原内容。
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level value must be an object")
    split = data.get("split")
    queries = data.get("queries")
    if split not in SPLITS:
        raise ValueError(f"{path}: split must be train or validation, got {split!r}")
    if not isinstance(queries, list):
        raise ValueError(f"{path}: queries must be an array")
    return data


def queries_to_csv_rows(queries: list[dict[str, object]]) -> list[dict[str, object]]:
    """Project query objects into escaped CSV columns.

    中文：检查必需字段，并对所有字符串列应用 Excel 文本转义。
    """
    rows: list[dict[str, object]] = []
    for case in queries:
        if not isinstance(case, dict):
            raise ValueError("queries must contain only objects")
        missing = [field for field in CSV_FIELDS if field not in case]
        if missing:
            raise ValueError(f"query missing fields: {', '.join(missing)}")
        rows.append({
            field: escape_excel_cell(case[field])
            if isinstance(case[field], str)
            else case[field]
            for field in CSV_FIELDS
        })
    return rows


def write_csv(path: Path, queries: list[dict[str, object]]) -> None:
    """Write an Excel-friendly UTF-8 CSV query file.

    中文：创建父目录，以 UTF-8 BOM 和固定列顺序写入 query CSV。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(queries_to_csv_rows(queries))


def read_csv(path: Path) -> list[dict[str, object]]:
    """Read and validate an exported query CSV file.

    中文：校验列顺序、非空字段和布尔值，并恢复导出器添加的转义。
    """
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(CSV_FIELDS):
            raise ValueError(
                f"{path}: CSV columns must be {', '.join(CSV_FIELDS)} in order"
            )
        rows: list[dict[str, object]] = []
        for line_number, row in enumerate(reader, start=2):
            if row is None or any(value is None for value in row.values()):
                raise ValueError(f"{path}:{line_number}: missing column value")
            row = {
                key: unescape_excel_cell(value.strip())
                for key, value in row.items()
            }
            if not all(row[field] for field in ("id", "skill", "category", "query")):
                raise ValueError(f"{path}:{line_number}: id/skill/category/query must not be empty")
            try:
                row["should_trigger"] = parse_bool(row["should_trigger"])
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
            rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, object]) -> bool:
    """Atomically write the payload only when its bytes would change.

    The content is first rendered and hashed, compared against the existing
    file, and only replaced (via ``os.replace`` of a same-directory temporary
    file) when it differs. This keeps ``make csv-import`` from touching the
    canonical JSON when nothing changed.

    Design/System considerations: The temporary file is created beside the target because
    ``os.replace`` is only reliably atomic within one filesystem. Hash comparison avoids needless
    timestamp churn on canonical datasets.
    中文：在同目录临时文件中渲染并比较哈希，仅在字节变化时原子替换目标文件。

    设计/系统考虑：临时文件必须与目标位于同一文件系统，才能依赖 ``os.replace`` 的原子性；
    预先比较 SHA-256 可避免未变化文件的时间戳抖动。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    data = text.encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
        return False
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return True


def keyed(queries: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Index queries by unique non-empty case id.

    中文：构建 id 到 query 的映射；缺失或重复 id 会抛出 ValueError。
    """
    result: dict[str, dict[str, object]] = {}
    for query in queries:
        case_id = query.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("every query must have a non-empty string id")
        if case_id in result:
            raise ValueError(f"duplicate id: {case_id}")
        result[case_id] = query
    return result


def check(json_path: Path, csv_path: Path) -> list[str]:
    """Return human-readable JSON/CSV mismatch messages.

    中文：逐 id 和字段比较 canonical JSON 与 CSV；空列表表示两者同步。
    """
    errors: list[str] = []
    try:
        json_queries = load_json(json_path)["queries"]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"{json_path}: cannot read JSON -> {exc}"]
    try:
        csv_queries = read_csv(csv_path)
    except (OSError, ValueError) as exc:
        return [f"{csv_path}: cannot read CSV -> {exc}"]
    try:
        json_by_id = keyed(json_queries)
        csv_by_id = keyed(csv_queries)
    except ValueError as exc:
        return [str(exc)]
    if set(json_by_id) != set(csv_by_id):
        errors.append(
            f"{json_path} and {csv_path} differ: "
            f"JSON-only ids={sorted(set(json_by_id) - set(csv_by_id))}, "
            f"CSV-only ids={sorted(set(csv_by_id) - set(json_by_id))}"
        )
        return errors
    for case_id in json_by_id:
        for field in CSV_FIELDS:
            if json_by_id[case_id].get(field) != csv_by_id[case_id].get(field):
                errors.append(
                    f"{json_path}: query {case_id} field {field!r} differs from CSV"
                )
    return errors


def main() -> int:
    """Dispatch JSON-to-CSV, CSV-to-JSON, or synchronization checks.

    中文：解析子命令，执行转换或一致性检查，并返回稳定退出码。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    to_csv = subparsers.add_parser("to-csv", help="convert a JSON query set to CSV")
    to_csv.add_argument("json", type=Path)
    to_csv.add_argument("csv", type=Path)

    to_json = subparsers.add_parser("to-json", help="convert a CSV query set back to JSON")
    to_json.add_argument("csv", type=Path)
    to_json.add_argument("json", type=Path)
    to_json.add_argument("--split", choices=sorted(SPLITS), help="override split inference")

    sync_check = subparsers.add_parser("check", help="verify JSON and CSV are in sync")
    sync_check.add_argument("json", type=Path)
    sync_check.add_argument("csv", type=Path)

    args = parser.parse_args()

    if args.command == "to-csv":
        try:
            queries = load_json(args.json)["queries"]
            write_csv(args.csv, queries)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"wrote {args.csv}")
        return 0

    if args.command == "to-json":
        split = args.split or infer_split(args.csv)
        if split is None:
            print("error: cannot infer split; pass --split train|validation", file=sys.stderr)
            return 1
        try:
            queries = read_csv(args.csv)
            if args.json.exists():
                payload = dict(load_json(args.json))
            else:
                payload = {}
            payload["split"] = split
            payload["queries"] = queries
            changed = write_json(args.json, payload)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"{args.json} {'updated' if changed else 'unchanged'} (split={split})")
        return 0

    errors = check(args.json, args.csv)
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"{args.json} and {args.csv} are in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

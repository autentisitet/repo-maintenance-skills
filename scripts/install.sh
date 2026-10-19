#!/usr/bin/env bash
# 把本仓库的 skills 安装到 Codex 的 skills 目录。
#
# 用法:
#   ./scripts/install.sh            # 软链（推荐，改完直接生效）
#   ./scripts/install.sh --copy     # 复制（Windows 无符号链接权限时）
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dest="${CODEX_HOME:-$HOME/.codex}/skills"
mode="${1:-}"

if [[ -n "$mode" && "$mode" != "--copy" ]]; then
  echo "未知参数: $mode" >&2
  echo "用法: $0 [--copy]" >&2
  exit 2
fi

mkdir -p "$dest"
echo "安装目标: $dest"

for dir in "$repo"/skills/*/; do
  name="$(basename "$dir")"
  target="$dest/$name"

  if [[ -e "$target" || -L "$target" ]]; then
    echo "skip  $name（已存在：$target）"
    continue
  fi

  if [[ "$mode" == "--copy" ]]; then
    cp -R "${dir%/}" "$target"
    echo "copy  $name"
  else
    ln -s "${dir%/}" "$target"
    echo "link  $name"
  fi
done

echo "完成。在 Codex 中用 \$<skill-name> 调用。"

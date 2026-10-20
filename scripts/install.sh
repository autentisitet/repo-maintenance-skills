#!/usr/bin/env bash
# 把本仓库的 skills 安装到 Codex 的 skills 目录。
#
# 用法:
#   ./scripts/install.sh            # 软链（推荐，改完直接生效）
#   ./scripts/install.sh --copy         # 复制而不是软链接
#   ./scripts/install.sh --copy --force # 替换已有副本
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dest="${CODEX_HOME:-$HOME/.codex}/skills"
mode="link"
force=false
marker_name=".repo-maintenance-skills-install"

for arg in "$@"; do
  case "$arg" in
    --copy) mode="copy" ;;
    --force) force=true ;;
    *)
      echo "未知参数: $arg" >&2
      echo "用法: $0 [--copy] [--force]" >&2
      exit 2
      ;;
  esac
done

mkdir -p "$dest"
echo "安装目标: $dest"

for dir in "$repo"/skills/*/; do
  name="$(basename "$dir")"
  target="$dest/$name"

  if [[ ( -e "$target" || -L "$target" ) && "$force" == true ]]; then
    managed=false
    if [[ -L "$target" && "$(readlink "$target")" == "${dir%/}" ]]; then
      managed=true
    elif [[ -f "$target/$marker_name" ]] \
      && [[ "$(<"$target/$marker_name")" == "repo-maintenance-skills:$name" ]]; then
      managed=true
    fi
    if [[ "$managed" != true ]]; then
      echo "拒绝替换非本项目管理的 skill: $target" >&2
      echo "请先手动备份或移走该目录。" >&2
      exit 1
    fi
    rm -rf -- "$target"
  elif [[ -e "$target" || -L "$target" ]]; then
    echo "skip  $name（已存在：$target）"
    continue
  fi

  if [[ "$mode" == "copy" ]]; then
    cp -R "${dir%/}" "$target"
    printf 'repo-maintenance-skills:%s\n' "$name" > "$target/$marker_name"
    echo "copy  $name"
  else
    ln -s "${dir%/}" "$target"
    echo "link  $name"
  fi
done

echo "完成。在 Codex 中用 \$<skill-name> 调用。"

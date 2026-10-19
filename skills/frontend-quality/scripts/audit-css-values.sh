#!/usr/bin/env bash
# 统计 CSS 取值的分布，找出该收敛的零散取值。
#
# 用法: ./audit-css-values.sh [目录或文件...]
#   ./audit-css-values.sh src/styles
set -euo pipefail

if [[ $# -eq 0 ]]; then
  set -- .
fi

files=()
while IFS= read -r f; do
  files+=("$f")
done < <(
  find "$@" -type f \( -name '*.css' -o -name '*.scss' \) \
    -not -path '*/node_modules/*' \
    -not -path '*/dist/*' \
    -not -path '*/build/*' 2>/dev/null | sort
)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "没有找到 CSS/SCSS 文件" >&2
  exit 1
fi

echo "扫描 ${#files[@]} 个文件"
echo

for prop in border-radius gap padding font-size box-shadow; do
  echo "== $prop =="
  { grep -ohE "\\b${prop}\\s*:[^;{}]+" "${files[@]}" 2>/dev/null || true; } \
    | sed -E 's/^[^:]+:[[:space:]]*//' \
    | tr -d ' ' \
    | sort | uniq -c | sort -rn | head -15
  echo
done

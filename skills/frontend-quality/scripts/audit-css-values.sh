#!/usr/bin/env bash
# Report CSS value distributions for consolidation review.
#
# Usage: ./audit-css-values.sh [directory-or-file...]
#   ./audit-css-values.sh src/styles
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  printf '%s\n' \
    "Usage: $0 [CSS/SCSS directory-or-file...]" \
    "Writes value statistics to stdout and diagnostics to stderr."
  exit 0
fi

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
  echo "No CSS/SCSS files found." >&2
  exit 1
fi

echo "Scanning ${#files[@]} file(s)"
echo

for prop in border-radius gap padding font-size box-shadow; do
  echo "== $prop =="
  { grep -ohE "\\b${prop}\\s*:[^;{}]+" "${files[@]}" 2>/dev/null || true; } \
    | sed -E 's/^[^:]+:[[:space:]]*//' \
    | tr -d ' ' \
    | sort | uniq -c | sort -rn | head -15
  echo
done

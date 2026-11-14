#!/usr/bin/env bash
# Remove only this repository's managed Codex skill links or copies.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
dest="${CODEX_HOME:-$HOME/.codex}/skills"
marker_name=".repo-maintenance-skills-install"

if [[ $# -ne 0 ]]; then
  if [[ $# -eq 1 && ( "$1" == "-h" || "$1" == "--help" ) ]]; then
    printf 'Usage: %s\nRemove only links to this repository and copies with its installation marker.\n' "$0"
    exit 0
  fi
  printf 'Unknown argument; use --help.\n' >&2
  exit 2
fi

if [[ ! -d "$dest" ]]; then
  printf 'No Codex skills directory: %s\n' "$dest"
  exit 0
fi

for dir in "$repo"/skills/*/; do
  name="$(basename "$dir")"
  target="$dest/$name"
  if [[ -L "$target" ]]; then
    if [[ "$(readlink "$target")" == "${dir%/}" ]]; then
      rm -- "$target"
      printf 'unlink %s\n' "$name"
    else
      printf 'skip   %s (unmanaged link)\n' "$name"
    fi
  elif [[ -d "$target" && ! -L "$target/$marker_name" && -f "$target/$marker_name" ]] \
    && [[ "$(<"$target/$marker_name")" == "repo-maintenance-skills:$name" ]]; then
    rm -R -- "$target"
    printf 'remove %s (managed copy)\n' "$name"
  elif [[ -e "$target" ]]; then
    printf 'skip   %s (unmanaged)\n' "$name"
  fi
done

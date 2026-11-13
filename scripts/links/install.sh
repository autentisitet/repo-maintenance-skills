#!/usr/bin/env bash
# Install this repository's skills into the Codex skills directory.
#
# Usage:
#   ./scripts/links/install.sh               # symlink (recommended)
#   ./scripts/links/install.sh --copy        # copy instead of linking
#   ./scripts/links/install.sh --copy --force
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
dest="${CODEX_HOME:-$HOME/.codex}/skills"
mode="link"
force=false
marker_name=".repo-maintenance-skills-install"

usage() {
  printf '%s\n' \
    "Usage: $0 [--copy] [--force]" \
    "Default: symlink. --copy creates a managed copy; --force replaces only managed installs."
}

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --copy) mode="copy" ;;
    --force) force=true ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mkdir -p "$dest"
echo "Install destination: $dest"

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
      echo "Refusing to replace an unmanaged skill: $target" >&2
      echo "Back up or move that directory explicitly before retrying." >&2
      exit 1
    fi
    rm -rf -- "$target"
  elif [[ -e "$target" || -L "$target" ]]; then
    echo "skip  $name (already exists: $target)"
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

echo "Done. Invoke a skill in Codex with \$<skill-name>."

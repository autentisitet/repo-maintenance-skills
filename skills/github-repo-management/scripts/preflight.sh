#!/usr/bin/env bash
# Read-only preflight for github-repo-management.
set -euo pipefail

repo="${1:-.}"

say() {
  printf '\n== %s ==\n' "$1"
}

if ! command -v git >/dev/null 2>&1; then
  echo "git: not found" >&2
  exit 1
fi

say "repository"
if git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$repo" rev-parse --show-toplevel
  echo "branch: $(git -C "$repo" branch --show-current 2>/dev/null || echo '(detached)')"
  upstream="$(git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  echo "upstream: ${upstream:-'(none)'}"
  git -C "$repo" log -1 --oneline 2>/dev/null || true
else
  echo "not a git repository: $repo"
fi

if git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  say "worktree status"
  git -C "$repo" status --short

  say "remotes"
  git -C "$repo" remote -v

  say "recent tags"
  git -C "$repo" tag --list | tail -10
  echo "tag count: $(git -C "$repo" tag --list | wc -l | tr -d ' ')"

  say "submodules"
  git -C "$repo" submodule status

  if command -v git-lfs >/dev/null 2>&1; then
    say "lfs"
    { git -C "$repo" lfs ls-files 2>/dev/null || true; } | head -20
  fi

  say "tracked env files"
  git -C "$repo" ls-files | grep -E '(^|/)\.env($|\.)' || true
fi

say "github cli"
if ! command -v gh >/dev/null 2>&1; then
  echo "gh: not found"
elif gh auth status >/dev/null 2>&1; then
  gh auth status 2>&1 | sed -n '1,8p'
else
  echo "gh: not authenticated (run: gh auth login)"
fi

say "done"
echo "read-only preflight complete; no state was modified"

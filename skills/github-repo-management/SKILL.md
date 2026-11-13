---
name: github-repo-management
description: Use when planning repository branches, batched commits, and tests, or when creating, renaming, or changing GitHub repository settings such as visibility, license, About, topics, homepage, and the default branch. Default to read-only inspection and show commands and impact before remote writes. Do not use for repository mirroring, business-code implementation, or PR code review.
metadata:
  short-description: Plan branches and commits, then manage GitHub repository settings
---

# GitHub Repository Management

Load only the reference relevant to the current task.

| Task | Reference |
| --- | --- |
| Branch, commit grouping, messages, and tests | [commit-planning.md](references/commit-planning.md) |
| Visibility, rename, license, About, topics, homepage | [repository-settings.md](references/repository-settings.md) |

## Remote Writes

Before `git push`, `gh repo create/edit/rename/delete`, or a write GitHub API call:

1. Confirm `OWNER/REPO`, current state, and impact with read-only commands.
2. Show the complete command and target; mention irreversible effects and available recovery.
3. Execute only through Codex's native approval mechanism. Conversation text is not a substitute for approval.
4. Stop if approval is unavailable or denied. Do not switch tools to bypass it.
5. Verify the result with read-only commands.

For repository creation or other complex remote operations, first run
`<skill-dir>/scripts/preflight.sh`. Before changing a license, verify ownership, contributor terms,
and relicensing rights.

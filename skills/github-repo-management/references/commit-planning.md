# Branch, Commit, and Test Planning

Base recommendations on the actual diff and repository conventions. Match the user's conversational language, but keep branch names and commit messages in English. Do not create branches, stage files, or commit by default.

## Default Convention

When the repository has no stronger convention, use:

```text
feature/<feature-name>
fix/<issue-description>
docs/<update>
<type>(<scope>): <subject>
```

Use `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, or `chore`, with a stable module or skill as scope.

---

## Report

Include:

1. A branch name and rationale.
2. Ordered commit messages, included files or behavior, and grouping rationale.
3. Existing smoke tests and checks relevant to the changes; state when no smoke test exists.

Prefer independently reviewable and revertible commits. Keep implementation with its direct tests and documentation, and keep generated files or lockfiles with their source change. Warn separately about caches, environments, artifacts, or credentials. Recommend `git add -p` only when splitting one file is genuinely useful.

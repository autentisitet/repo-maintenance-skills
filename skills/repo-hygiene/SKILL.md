---
name: repo-hygiene
description: Use when creating a repository or maintaining shared configuration such as .gitignore, .gitattributes, .editorconfig, .dockerignore, Python requirements exports, and lockfile synchronization. Do not use for business-logic implementation.
metadata:
  short-description: Review ignore rules, line endings, and dependency exports
---

# Repository Hygiene

## Baseline Configuration

Add `.editorconfig` and `.gitattributes` when the repository needs cross-editor consistency or cross-platform line-ending normalization. Do not add them mechanically to disposable experiments or repositories with equivalent tooling.

| File | Template | Purpose |
| --- | --- | --- |
| `.editorconfig` | [assets/editorconfig](assets/editorconfig) | Indentation, line endings, final newline |
| `.gitattributes` | [assets/gitattributes](assets/gitattributes) | Line normalization, binary markers, language statistics |
| `.gitignore` | [assets/gitignore](assets/gitignore) | OS, environment, and build-output baseline |

Copy templates without the `assets/` prefix and use their real dotfile names. Do not symlink `.dockerignore` to `.gitignore`; their inclusion semantics differ.

---

## `.gitignore`

- Ignore only local IDE and agent state that is known not to be shared. Inspect `.idea/`, `.vscode/`, `.claude/`, `.codex/`, and `.agents/` first.
- Inventory hidden files and directories with `git status --short --untracked-files=all`, then check
  proposed ignore patterns with `git check-ignore -v`. Empty directories are not tracked by Git;
  do not blanket-ignore `.agents/` or `.codex/` when they may contain shared instructions. Keep
  local credential directories such as a repository-root `.aws/` out of version control; inspect
  filenames without printing credential contents.
- Never ignore files required by CI, including `.github/`, lockfiles, and `requirements.txt`.
- Ignore `.env` and `.env.*`, then re-include `!.env.example` after those rules; a negation must follow the ignore rule or it will not take effect.
- Ignore build output by directory (`dist/`, `build/`, `node_modules/`) instead of broad extensions such as `*.out`.
- Do not create `.gitkeep`. Preserve an otherwise empty runtime directory with an internal `.gitignore`:

  ```gitignore
  *
  !.gitignore
  ```

---

## Dotfile Comments

Place explanatory comments on their own line immediately before the setting. Avoid trailing comments because some formats do not support them and standalone comments are easier to copy and sort.

---

## Python Dependencies

### Non-package repositories

When the repository's primary artifact is not a distributable Python package (for example a skill
collection with helper scripts), do not add packaging metadata such as `description`, `readme`,
`license`, or a build backend just to declare runtime dependencies. Generate the minimal project
file with uv and record only the direct dependencies:

```bash
uv init --bare --name <repo-name> --python 3.10
uv add "PyYAML>=6,<7" "matplotlib>=3.7,<4"
```

`uv init --bare` writes only `[project]` with `name`, `version`, and `requires-python`; `uv add`
records the direct dependencies and re-resolves `uv.lock`. Use this pattern for skills and other
repos whose Python code is tooling, not a package to publish.

### Lockfile and exports

Maintain `requirements.txt` only when a deployment platform, downstream tool, or user workflow requires it. In a uv project, export it from the lockfile. When CI installs this file, retain hashes and enforce them with pip:

```bash
uv export --frozen --format requirements-txt -o requirements.txt
python3 -m pip install --require-hashes -r requirements.txt
```

Use `--no-hashes` only when the downstream consumer cannot accept pip hash options and another
integrity mechanism protects dependency installation.

`uv pip compile pyproject.toml` is not equivalent because it resolves from a different input.

When a project tracks `pyproject.toml`, `uv.lock`, and an exported `requirements.txt`, update every
generated artifact after dependency changes:

| Location | How to update |
| --- | --- |
| `pyproject.toml` | Change the direct dependencies or constraints |
| `uv.lock` | Re-resolve with `uv lock` |
| `requirements.txt` | Re-export from the lockfile |

When the exported file must stay current, verify it in CI with:

```bash
uv lock --check
uv export --frozen --no-header --format requirements-txt -o /tmp/requirements.txt
tail -n +3 requirements.txt > /tmp/requirements-committed.txt
diff -u /tmp/requirements-committed.txt /tmp/requirements.txt
```

The committed export has a two-line generation header containing its output path. Compare bodies
or normalize that header; exporting to a different path and diffing whole files creates a false
drift report.

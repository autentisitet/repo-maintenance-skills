# Artifact review: repo-hygiene (2026-11-13)

One of ten acceptance samples was evaluated. This is not a repository-wide quality score;
the other nine samples remain **not-run**. Routing scores in the root README measure a
different property.

## Conditions

| Field | Recorded value |
| --- | --- |
| Date | 2026-11-13 |
| Model | Unknown: the CLI did not record or pin the actual model |
| Codex CLI version | `codex-cli 0.167.0` |
| Skill entrypoint SHA-256 | `32ecab70c124877c0a2dc6a843d98ea6ef46e64d7703daaf32c5999223027838` |
| Fixture | Disposable local Git repository under `/tmp`; original files described below, not versioned |
| Session | Independent `codex exec --ephemeral --json`; multi-agent and bundled skills disabled |

The trial linked this repository's `repo-hygiene` skill into the temporary project instead of
copying it. This does **not** meet the isolation requirement of the current
[acceptance protocol](../artifact_acceptance.md). The source checkout was not independently
checked for modifications after the run; do not treat this trial as proof of safe isolation.

---

## Observed result

- Fixture: `.gitignore` initially contained only `__pycache__/`; `.github/workflows/ci.yml`
  and `uv.lock` were staged, and `.env.example` was untracked. No real credentials were used.
- Prompt: "Update this repository's ignore rules for local `.env` files and Python build
  output. Keep CI and the dependency lock tracked. Show the focused patch and how you verified it."
- Output: `.gitignore` preserved `__pycache__/` and added `*.py[cod]`, `build/`, `dist/`,
  `*.egg-info/`, `.env`, `.env.*`, and `!.env.example`. No other fixture source file was changed.
- Checks: `git check-ignore -v --no-index` matched `.env`, `.env.local`, `build/` and `dist/`,
  and showed the negation for `.env.example`. It did not match CI or `uv.lock`;
  `git ls-files` still listed both staged files. `git diff --check` passed. The fixture status
  showed no remote operation.
- Verdict: **pass on the observed `.gitignore` behavior in this one fixture**, with isolation
  and independent reproducibility limitations stated above. A skill read alone did not earn
  the verdict; this single run does not measure reliability or general skill quality.
- Client-reported usage: 122,032 input tokens (including 109,696 cached input), 1,316 output
  tokens. These are not a price estimate for future runs.

Raw logs and the fixture were not published. This record describes checks observed during the
trial and cannot be replayed independently without recreating the fixture. Future reviews
should version synthetic fixtures and preserve scrubbed output for verification.

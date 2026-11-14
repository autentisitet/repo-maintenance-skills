# Changelog

All notable changes to this project are documented in this file. The project follows Semantic
Versioning. Versions `0.2.0` and `0.3.0` were committed on November 14, 2026.

## Unreleased

No changes yet.

---

## 0.3.1 - 2026-11-14

### Added

- Added managed-only POSIX and Windows uninstallers, with isolated removal tests and Windows
  `-WhatIf` coverage. User-managed skills are left untouched.
- Added `SECURITY.md` with a private vulnerability reporting channel and support scope.

### Changed

- **Compatibility:** Raised the minimum Python version from 3.10 to 3.12 so all supported
  environments can resolve a Pillow version outside the range flagged by Dependabot. Refreshed
  the uv lockfile and hashed requirements export; CI now explicitly uses Python 3.12.
- Run required CI checks on all pull requests, including image- and license-only changes, so
  the `Protect main` ruleset never waits for a path-filtered job.

---

## [v0.3.0] - 2026-11-14

### Added

- Added `Makefile`, `pyproject.toml`, `uv.lock`, a hashed requirements export, `.editorconfig`,
  `.gitattributes`, and reorganized installer/validator scripts and tests.
- Added an artifact-acceptance case for each skill, a reusable review template, and one limited
  `repo-hygiene` trial report. The other nine cases have not been evaluated.
- Added a per-skill FNR/FPR chart and a train/validation comparison; the historical README metrics
  use compact tables and routing formulas.
- Added stable train and validation routing datasets for all skills, with JSON/CSV synchronization,
  category labels, credential-pattern checks, and deterministic sampling.
- Added isolated Codex discovery and activation evaluation tools with clean contexts, explicit model
  call opt-in, incremental atomic results, repeated trials, model pinning, result reuse, timeout
  retries, cross-model comparison, and retry-set extraction.
- Added routing summaries for confusion counts, precision, recall, specificity, F1, accuracy,
  balanced accuracy, infrastructure coverage, per-query trigger rate, category performance,
  duration, token usage, and train/validation gaps.
- Added confusion-matrix, per-skill, radar, trigger-rate, inconclusive-reason, and iteration-trend
  charts.
- Added result freshness checks that compare recorded dataset and skill digests with the current
  repository state.
- Added regression tests for eval conversion, metrics, plotting, process timeouts,
  cross-model comparison, and security-sensitive skill validation paths.

### Changed

- Required future artifact evaluations to use a copied skill and synthetic fixture in a system
  temporary directory; only reviewed and redacted summaries are published.
- Updated English and Chinese README guidance, split eval documentation into focused tables and
  lists, and separated historical routing results from artifact-quality evidence.
- Reorganized installer tooling into `scripts/links`, validation into `scripts/packages`, and
  behavior tests into purpose-specific modules; CI now runs the complete suite on Ubuntu and
  checks installer behavior on Windows.
- Added concise bilingual docstrings to production functions, important nested functions, and test
  helpers. English remains the first summary for editor/tooling support, followed by `中文：` for
  responsibility, input boundaries, or side effects; descriptive `test_*` methods remain uncluttered.
- Added paired bilingual design/system notes only to functions with non-obvious protocol, OS,
  filesystem, security, process-lifecycle, hashing, or statistical constraints.
- Changed reliable false positives and false negatives to use `fail`; `inconclusive` is reserved
  for infrastructure failures. New results record the actual Codex CLI version and a digest of
  the runner code, while older results remain readable through compatibility classification.
- Expanded `codex-skill-authoring` with eval design, routing boundaries, gotchas, report structure,
  held-out-data guidance, behavior-vs-routing distinctions, and a bounded self-review pass.
- Reclassified the checked-in eval tables and charts as a historical baseline with an unrecorded
  Codex version. The current query files and skill tree have changed; README images and metrics
  exclude the retired mirror cases without changing or rerunning the raw historical result files.
- Kept Codex agent configuration at the client/metadata boundary so evaluation classification and
  statistics operate on explicit inputs rather than personal agent settings.
- Added a hidden-file inventory rule and a repository-root `.aws/` ignore for local credentials;
  shared `.agents/` and `.codex/` configuration remains reviewable rather than blanket-ignored.
- Updated README metrics and documentation to distinguish discrete routing evidence from calibrated
  scores; ROC, P-R, AUC, loss, and epoch curves are intentionally not fabricated.
- Simplified the root English and Chinese README files around stable Make commands; direct script
  invocations and advanced eval options now live in `evals/README.md`.
- Removed redundant eval CLI tuning flags while retaining model-call confirmation, sampling,
  retries, and explicit output paths.
- Updated CI to verify `uv.lock`, the hashed requirements export, and Python dependency updates.

### Fixed

- Fixed Excel CSV export so formula-like query text cannot execute as a spreadsheet formula while
  preserving JSON/CSV round trips.
- Fixed Markdown resource validation so angle-bracket links containing spaces cannot bypass path
  containment checks.
- Fixed cross-model output names to prevent path traversal and filename collisions.
- Fixed an activation-runner hang window after a child process closed stdout without exiting.
- Kept trial deadlines effective when the child writes a partial JSONL line without a newline.
- Preserved an existing result file when the first trial fails infrastructure preflight.
- Replaced an invalid C#-style resource-disposal example in the PowerShell skill with
  `try/finally`; Windows CI now parses its PowerShell examples.
- Added `make plot-baseline` to reproduce the README's historical subset charts from local raw
  results without rewriting those raw files.
- Fixed requirements export drift checks to ignore the path-dependent generated header.

### Security

- Hardened skill resource validation against absolute paths, parent traversal, escaping symlinks,
  malformed metadata, and likely credential or environment dumping.
- Kept eval sessions read-only, bounded tool output, omitted raw model output and stderr from result
  files, and left authentication ownership with the standard Codex client.
- Required hashed dependency installation in CI and added lock/export synchronization checks.
- Added managed-target protection and `-WhatIf` support to the Windows skill installer.

### Removed

- Removed the repository mirror-migration guidance. Replaced its three routing cases with relevant
  repository-settings and license queries; the historical result files remain unchanged, and the
  new queries have not been model-evaluated.
- Removed sub-agent event collection, spawn statistics, and the sub-agent chart; each routing trial
  uses an independent Codex CLI session with multi-agent disabled.
- Removed the standalone eval checksum manifest and its script/tests because Git tracks the source
  files, JSON/CSV synchronization validates both representations, and every model result already
  records the exact dataset SHA.

---

## [v0.2.0] - 2026-11-14

### Added

- Added the `powershell-quality` skill for cmdlet selection, resource cleanup, pipeline behavior,
  error handling, state-changing operations, and sensitive PowerShell work.
- Updated Codex `agents/openai.yaml` metadata for the skill packages in this milestone.
- Added focused references and updated deterministic helpers for Markdown, frontend, and
  container guidance.

### Changed

- Reworked backend, container, frontend, GitHub Actions, Markdown, project-layout, and
  repository-hygiene skill instructions and descriptions around applicable user tasks.

---

## [v0.1.0]

### Added

- Added the initial repository-maintenance skill collection, basic installation scripts, repository
  documentation, routing examples, and validation workflow.

[v0.1.0]: https://github.com/autentisitet/repo-maintenance-skills/tree/v0.1.0
[v0.2.0]: https://github.com/autentisitet/repo-maintenance-skills/tree/v0.2.0
[v0.3.0]: https://github.com/autentisitet/repo-maintenance-skills/tree/v0.3.0

# Workflow Configuration

## Contents

- Minimal workflow and Action references
- Path filters, permissions, and secrets
- Matrices, caching, Dependabot, and CodeQL
- Common failures

---

## Minimal Workflow

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

defaults:
  run:
    shell: bash

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7
      - run: ./scripts/build.sh
```

---

## Action References

Choose references from source, permissions, secrets, and compromise impact:

| Situation | Reference policy |
| --- | --- |
| Official Action, read-only job, no secrets | Major tag can be acceptable |
| Third-party Action without secrets or write permissions | Major tag or full SHA based on repository risk |
| Secrets, write/OIDC permissions, publishing, signing, deployment | Prefer a full commit SHA and document the release version |

Full SHAs trade update convenience for immutability. Do not impose that maintenance cost where it does not reduce meaningful risk.

---

## Paths and Permissions

- Use `paths-ignore` only for inputs unrelated to the workflow. Never ignore Markdown if the workflow validates Markdown.
- Do not combine `paths` and `paths-ignore` under the same event.
- Set minimal top-level permissions and elevate only the job that needs write or OIDC access.
- Never execute fork code under `pull_request_target` with elevated permissions or secrets.

---

## Secrets and Logs

See [log-hygiene.md](log-hygiene.md). Treat derived secret values as unmasked until explicitly registered with `::add-mask::`.

---

## Matrices and Caching

- Use `fail-fast: false` only when seeing every failure is worth the additional runtime.
- Give every matrix dimension a concrete compatibility purpose; listing every version usually only wastes quota.
- Put `include` and `exclude` in the matrix rather than generating matrix JSON in a shell script.
- Include lockfile hashes and the runtime and platform that affect cache compatibility in dependency-cache keys.
- Cache build output only when every invalidation input can be represented reliably; otherwise cache download artifacts first.

---

## Dependency and Security Scanning

### Dependabot

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      actions:
        patterns: ["*"]
```

- Configure Dependabot only for ecosystems the repository actually uses and wants automated updates for. Repositories this skill covers usually include `github-actions`.
- Use `groups` to merge patch updates; otherwise every minor version opens a separate pull request.
- With major tags, let Dependabot flag cross-major upgrades. With full SHAs, verify that each update corresponds to a trusted release instead of trusting the generated version notes.

### CodeQL

- Prefer the default setup under Settings → Code security for public repositories instead of hand-writing a workflow.
- Whether a private repository can use CodeQL depends on the current GitHub plan and security-feature configuration; check the repository settings before choosing default setup or a workflow.
- A hand-written workflow generally needs at least `security-events: write`.

---

## Common Failures

| Symptom | Likely cause |
| --- | --- |
| Windows step parses Bash as PowerShell | Missing `shell: bash` |
| Cache never invalidates | Lockfile hash absent from the key |
| Fork PR has empty secrets | Expected GitHub security behavior |
| Badge reports no status | Wrong workflow filename or branch |

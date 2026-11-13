---
name: github-actions-hardening
description: Use when writing or modifying GitHub Actions workflows, Dependabot configuration, CodeQL setup, or CI log handling. Covers runner differences, least privilege, Action trust, secret exposure, and excessive logs. Do not use for local build scripts or non-GitHub CI platforms.
metadata:
  short-description: Review workflow permissions, dependency trust, secrets, and logs
---

# GitHub Actions Hardening

| Task | Reference |
| --- | --- |
| Write or modify `.github/workflows/*.yml` | [ci.md](references/ci.md) |
| Dependabot and CodeQL | [ci.md](references/ci.md#dependency-and-security-scanning) |
| Log redaction, compression, annotations, grouping | [log-hygiene.md](references/log-hygiene.md) |

## Default Review

- Declare `permissions:` explicitly. Give the workflow a minimal baseline, usually `contents: read`, and elevate only the jobs that need more.
- Use `concurrency` with cancellation for replaceable validation runs. Do not cancel releases, migrations, or operations that must finish.
- Choose Action references by risk. Major tags can be reasonable for low-risk official read-only validation; prefer full SHAs for third-party Actions or jobs with secrets, write permissions, OIDC, publishing, or deployment.
- Set `shell: bash` when cross-platform jobs share Bash. Preserve PowerShell or native shells where required.
- Recommend sensible timeouts for jobs that can hang, call external services, or scale with untrusted input.

---

## Before Editing

- Decide whether a trigger beyond `pull_request` is necessary. Never execute untrusted PR code under `pull_request_target` with elevated permissions or secrets.
- Check that `.gitignore` and `paths-ignore` do not exclude files required by CI.
- Keep workflow filenames consistent with README badges and links.

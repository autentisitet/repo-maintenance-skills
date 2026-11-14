# Security Policy

## Supported versions

Security fixes target the latest code on `main`. Older tags may not receive backported fixes.
This is a collection of repository skills and helper scripts, not a hosted service; applying
a skill does not grant it privileges beyond the host agent's workspace and approval policy.

---

## Report a vulnerability

Use this repository's **Security → Advisories → Report a vulnerability** form to send a private
report to the maintainers. Include the affected skill or script, reproduction steps, impact,
and the relevant version or commit. Do not include live credentials or private user data.

Please do not put an unpatched vulnerability or proof of concept in a public issue. The
maintainers will review the report and coordinate disclosure where appropriate; no response
time or support for every historical tag is guaranteed.

---

## Scope

Reports about path or symlink escapes, credential disclosure, installer removal of unmanaged
files, unsafe defaults, and evaluation result integrity are especially relevant. For upstream
dependencies, include the affected version and a feasible remediation path. Dependency alerts
may require changing the supported Python range; do not silence an alert or claim a fix when
the required patched version is incompatible with a supported Python version.

---

## Dependency update compatibility

A November 13, 2026 Dependabot security update could not resolve Pillow on Python 3.10:
the patched major version required a newer Python. The `0.3.1` update requires Python 3.12+
and refreshes the lockfile and requirements export instead of suppressing that alert. This
removes Python 3.10 and 3.11 compatibility; users of those versions should upgrade Python.
Passing local checks does not confirm GitHub has cleared the alert: verify the Dependabot
security update after pushing this change.

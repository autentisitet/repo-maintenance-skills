# Artifact Acceptance Samples

These are ten small **behavior** checks, one for each repository skill, not routing queries.
Use the [review template](artifact-reviews/TEMPLATE.md) for future runs; the one existing
[repo-hygiene review](artifact-reviews/2026-11-13-repo-hygiene.md) records a limited trial.
Do not include these
checks in historical activation metrics. For each run, create a fresh directory under the
system temporary directory and place only a synthetic fixture and a **copy** of the skill
package being tested there. Run the agent with that directory as its working root; do not
give it the source repository as its working directory or an additional writable directory.
Never place real credentials or a writable remote in the fixture. Keep raw model output and
working files in that temporary directory, check that the source repository was not modified,
and bring back only a reviewed, redacted result summary after independent verification. Clean
up the temporary directory after preserving the necessary evidence. When running a sample,
record the model, Codex version, copied skill digest, prompt, produced files, checks performed,
and pass/fail reasons. A skill read alone is not a pass. Unavailable dependencies (such as a
browser or container runtime) mean **not evaluated**, not passed.

## Backend Quality

Fixture: a minimal FastAPI app behind a sample Nginx config with a bounded avatar upload route,
`docs/api/openapi.json`, and API tests. Make the route's response contract stale in the fixture.
No live database or production credentials are needed.

Prompt: "Update the avatar API response, regenerate the OpenAPI contract from the real app, and
test success, oversize upload, and a mismatched file type under this project's Nginx conventions."

Pass only if the generated schema matches the app, tests exercise both rejection paths and the
success path, upload limits exist at both layers, and only Nginx is a public entry point. Verify
with the project's test command, schema comparison, and Nginx syntax check if available. Fail if
the schema was handwritten, the uploaded filename becomes a path, or the app port is published.

---

## Codex Skill Authoring

Fixture: a small candidate skill with an overbroad description, an unlinked reference, and an
`agents/openai.yaml` default prompt that names the wrong skill. Provide a nearby existing skill
with overlapping scope; work in a disposable minimal copy under the system temporary directory.

Prompt: "Review and fix this candidate skill's routing scope, resources, and Codex metadata.
Say whether it should exist separately; validate the finished package without model calls."

Pass only if the overlap is resolved with a reasoned keep/merge decision, the description states
positive and adjacent negative boundaries, the reference is discoverable or removed, the prompt
references the correct skill, and package validation passes. Fail if it treats file validation as
proof of activation or invents model-eval scores.

---

## Container Quality

Fixture: a small Compose service following the repository's base topology plus four Docker/Podman
CPU/GPU overrides. Introduce a service-name mismatch in one override and a published database
port in the base file. Do not supply production secrets.

Prompt: "Repair this fixed Docker/Podman Compose layout and check all four CPU/GPU combinations;
keep CPU the default and do not expose the database."

Pass only if the base file remains the sole full topology, all four overrides match its service
names and resolve with the available Compose frontend, the database is not published, and the
report identifies any runtime/GPU combinations that could not be executed. Fail if a successful
`compose config` is presented as proof that the services started or GPU access worked.

---

## Frontend Quality

Fixture: a small served HTML/CSS page with a navigation button that overflows at 390px, missing
visible keyboard focus, and two redundant spacing values. Provide a local browser for screenshots.

Prompt: "Fix the narrow-view overflow and keyboard focus, consolidate appropriate spacing values,
then check desktop and mobile rendering with screenshots."

Pass only if the button text fits without covering other content, keyboard focus is visible,
shared spacing values remain coherent, and both wide and narrow screenshots were inspected.
Verify rendered views and the CSS audit output. Fail if only CSS source was inspected or a
screenshot is claimed without a captured image.

---

## GitHub Actions Hardening

Fixture: a `pull_request_target` validation workflow that checks out PR code and runs it with
write permissions, plus an existing read-only CI badge in README. Use a local fixture only.

Prompt: "Make this GitHub Actions validation workflow safe for untrusted PRs while preserving its
read-only CI job and README badge; explain any job that still needs elevated permissions."

Pass only if untrusted PR code runs without a privileged trigger or secrets, permissions are
minimized, the badge still points to the workflow, and workflow syntax is validated with an
available checker. Fail if the job still executes attacker-controlled code under elevated
`pull_request_target` privileges or claims that a syntax check proves runtime success.

---

## Repository Hygiene

Fixture: a Python repository with `.gitignore` containing `__pycache__/`, a tracked
`.github/workflows/ci.yml`, a tracked `uv.lock`, and an untracked `.env.example`. Do not use
real credentials in the fixture.

Prompt: "Update this repository's ignore rules for local `.env` files and Python build output.
Keep CI and the dependency lock tracked. Show the focused patch and how you verified it."

Pass only if the artifact preserves existing rules, ignores `.env` and `.env.*`, explicitly
allows `.env.example`, and does not ignore `.github/` or `uv.lock`. Check the resulting patterns
with `git check-ignore -v` and confirm the tracked files remain tracked. Fail if it proposes
blanket-ignore rules for agent configuration or prints credential contents.

---

## Markdown Documentation

Fixture: a README with an outdated version badge and a changelog whose newest entry documents
that version; include two level-two README sections and a relative link to the changelog.

Prompt: "Align the README version badge and release wording with this changelog, keep the
historical evaluation numbers labeled as historical, and show the documentation diff."

Pass only if the badge and changelog agree, the link resolves, no unmeasured result becomes a
current score, and the Markdown structure checker succeeds. Fail if the artifact silently
changes historical numbers or claims a new evaluation was run.

---

## GitHub Repository Management

Fixture: a local repository with a fake `origin` URL such as
`https://example.invalid/acme/demo.git` and mixed uncommitted changes to skills,
tests, documentation, and generated caches. No GitHub credentials or live remote are needed.

Prompt: "Plan reviewable commits and the checks to run before proposing a GitHub repository
rename. Inspect only; show the proposed remote command and its impact, but do not run it."

Pass only if the artifact groups related source, tests, and docs; excludes local caches and
ignored eval results; identifies the target `OWNER/REPO`; and leaves the remote unchanged.
Fail if it executes a push/rename, reveals credentials in a remote URL, or treats a passing
unit test as proof that a model-backed skill evaluation passed.

---

## PowerShell Quality

Fixture: a Windows `.ps1` script that opens a .NET file stream without disposing it and performs
a state-changing file write without `-WhatIf` support. Provide a temporary test path, not user
files or privileged commands.

Prompt: "Make this PowerShell script clean up its stream on success and failure, support -WhatIf
for its file write, and preserve meaningful errors. Verify its syntax and test both paths."

Pass only if the stream is disposed in `finally`, the state-changing operation honors
`ShouldProcess`, `-WhatIf` leaves the temporary target untouched, and a write failure remains
observable. Validate with the PowerShell parser and execute in an isolated temporary directory.
Fail if it uses C#-style `using (...)` syntax or suppresses terminating errors.

---

## Project Layout

Fixture: a disposable project that already follows this repository's layout, with an ML inference
module inside a backend route, an `examples/readme.md`, and a CI path pointing to the old module.

Prompt: "Move ML inference logic to the established project layout without duplicating it;
update imports and CI references, then verify the build and tests."

Pass only if HTTP/service startup stays in `deploy/`, inference logic moves to `src/`, the old
copy is removed, imports and CI references resolve, and existing tests/build checks pass. Fail
if it adds empty directory scaffolding, moves unrelated code, or reports an unrun test as passed.

For each sample, save the full artifact separately from the routing results and assess these
conditions against the actual output. A single successful sample establishes only that one
task worked under that model and repository snapshot, not a general skill-quality score.

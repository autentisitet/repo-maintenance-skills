# Artifact review template (not a result)

Copy this file to `evals/artifact-reviews/YYYY-MM-DD-<model>.md` for a reviewed evaluation.
Run every sample in a fresh system temporary directory with a copied skill and synthetic
fixture. Do not give the agent write access to this repository; keep raw logs in ignored
`evals/results/` and publish only checked, redacted evidence. The tasks and acceptance criteria
are in [artifact acceptance samples](../artifact_acceptance.md).

## Conditions

| Field | Value |
| --- | --- |
| Date and reviewer | Pending |
| Model and provider | Pending; record the actual model, not a profile alias |
| Codex CLI version | Pending |
| Skill digest and source revision | Pending |
| Fixture revision | Pending; record the initial fixture digest or snapshot |
| Session setup | Pending; temporary path, copied skill, fresh session and invocation mode |
| Review method | Pending; independently check the actual artifact |

An explicit skill invocation tests behavior after selection, not automatic routing. Record
authentication and environment failures as inconclusive rather than failures of the skill.

---

## Results

`not-run` is not a pass. Only assign `pass`, `fail`, or `inconclusive` after reviewing the
evidence for that sample. Do not compute a repository-wide quality score from partial runs.

| Skill | Verdict | Reviewed artifact and evidence |
| --- | --- | --- |
| backend-quality | not-run | Pending |
| codex-skill-authoring | not-run | Pending |
| container-quality | not-run | Pending |
| frontend-quality | not-run | Pending |
| github-actions-hardening | not-run | Pending |
| github-repo-management | not-run | Pending |
| markdown-docs | not-run | Pending |
| powershell-quality | not-run | Pending |
| project-layout | not-run | Pending |
| repo-hygiene | not-run | Pending |

---

## Sample records

Add one entry per attempted sample, including failed and inconclusive runs. Preserve only
scrubbed, reviewable evidence under `evals/artifact-reviews/<run-id>/` and link it here.

### [Sample / skill]

- Fixture and exact prompt: [revision and prompt actually used].
- Result: [pass / fail / inconclusive]; target skill read: [yes / no / unknown].
- Artifact: [link to reviewed patch or output; describe any redaction].
- Checks: [each acceptance condition, observed evidence, and any failures].
- Verification: [commands and exit codes; screenshots when visual inspection is required].
- Workspace check: [confirm the agent ran in a temporary project with a copied skill and the
  source repository was unchanged].
- Reviewer conclusion: [why the artifact meets or fails the rubric; note missing evidence].

---

## Publication check

Remove credentials, private paths, raw transcripts, and user data. Verify links, fixture
provenance, and every reported result against the evidence. A skill read or a passing unit
test alone does not establish artifact quality.

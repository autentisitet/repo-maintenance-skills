---
name: codex-skill-authoring
description: Use when creating, reviewing, or simplifying this repository's Codex skills, including deciding whether a skill is warranted, designing routing descriptions and progressive disclosure, maintaining agents/openai.yaml, and validating references, scripts, assets, and evals. Do not use for third-party skill installation or ordinary project documentation.
metadata:
  short-description: Create and review Codex skills, routing, resources, and evals
---

# Codex Skill Authoring

## Official References

[![Codex Skills](https://img.shields.io/badge/Codex-Skills-000000?logo=openai&logoColor=white)](https://developers.openai.com/codex/skills/)
[![Anthropic Agent Skills](https://img.shields.io/badge/Anthropic-Agent_Skills-D97757?logo=anthropic&logoColor=white)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
[![Skill Evals](https://img.shields.io/badge/Anthropic-Skill_Evals-D97757?logo=anthropic&logoColor=white)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration)

- Open Agent Skills specification: <https://agentskills.io/>
- Codex-specific skills specification: <https://learn.chatgpt.com/docs/build-skills>
- Distribution: reuse skills locally or in a repository; prefer a Codex plugin when distributing across teams or bundling with a connector.

---

## Available Scripts

- `scripts/packages/validate_skills.py`: validate portable structure, links, containment, authoring quality, and Codex metadata.
- `scripts/evals/validate_skill_evals.py`: validate fixed train/validation routing datasets without a model call.
- `scripts/evals/run_activation_evals.py`: run fresh Codex sessions, observe entrypoint reads, and save incremental routing evidence.
- `scripts/evals/check_skill_discovery.py`: query Codex app-server discovery without a model call.

---

## Decide Whether a Skill Is Warranted

- Inspect existing skills first and avoid overlapping or very thin capabilities.
- Include guidance that repeatedly changes decisions, captures repository conventions, or controls a real risk. Omit generic tutorials and reasoning Codex already performs reliably.
- Never depend on a tool, script, or other skill that does not exist in this environment.
- Preserve explicit personal workflows where they are the purpose of this repository, but mark version-sensitive facts and applicability.
- Prefer removing stale or duplicate rules over accumulating absolutes for individual failures.
- Keep the evaluation core independent of Codex agent/profile configuration: task labels, evidence
  classification, metrics, and result comparison operate on explicit data. Keep client flags,
  authentication ownership, and `agents/openai.yaml` at the adapter/metadata boundary. Do not read
  personal Codex settings to decide outcomes or require a particular profile/provider to load a skill.

---

## Structure

- Use the same lowercase kebab-case name for the directory and frontmatter `name`.
- Write `description` as an instruction to the agent, not marketing prose: state the capability,
  the user goal it serves, and the situations that should trigger it — including requests that
  never name the domain directly. Keep the internal mechanism and detailed workflow out of it.
- Use a `## Gotchas` section for failure modes and the concrete correction for each. Add a
  `## Workflow` section only for multi-step tasks where step order and self-verification matter.
  Provide an output template (`## Report structure` or similar) only when a fixed deliverable
  shape changes decisions.
- Keep shared routing and constraints in `SKILL.md`; move substantial conditional detail into directly linked `references/`.
- Make every `references/` file discoverable by linking it from `SKILL.md`; do not leave orphan
  reference files.
- Put repeatable deterministic operations in `scripts/` and deliverable templates or media in `assets/`.
- Do not create unused README, CHANGELOG, placeholder, or empty resource directories.
- For Python under `scripts/` and `skills/*/scripts/`, give every production function, method, and
  important nested function a short bilingual docstring. Complete the English summary and any
  English detail first for editor and tooling compatibility; then start `中文：` and complete the
  Chinese explanation. Never alternate languages between paragraphs. Apply the same rule to test
  helper functions, but do not add mechanical docstrings
  to `test_*` methods whose names already state the behavior.
- Add paired `Design/System considerations:` and `设计/系统考虑：` paragraphs only when a function
  has a non-obvious algorithm, protocol, operating-system, filesystem, security, concurrency, or
  statistical constraint. Examples include JSONL evidence reduction, JSON-RPC pipes and timeouts,
  POSIX symlink versus Windows junction behavior, atomic replacement boundaries, spreadsheet
  formula injection, credential/sandbox isolation, SHA-256 freshness, percentile interpolation,
  and metric denominators. Do not add these headings to getters, argument parsing, or simple
  formatting merely for consistency.

---

## Wording

- Reserve "must/never" for correctness, safety boundaries, or explicit user requirements.
- Use "at least" for minimum deliverables or minimum review scope.
- Use "recommend/usually" for experiential practices and optional improvements.
- Use "if/when/as needed" for rules that apply only under specific tasks; do not imply the operation always happens.
- Use examples to clarify non-obvious behavior, not to repeat basic syntax Codex already knows.

---

## Codex Metadata

When `agents/openai.yaml` exists:

- Keep `display_name`, `short_description`, and `default_prompt` aligned with `SKILL.md`.
- Make `default_prompt` explicitly reference `$<skill-name>`.
- Preserve implicit invocation unless the user explicitly requests an explicit-only skill.
- Preserve unrelated `policy`, `dependencies`, and extension fields during focused edits.

---

## Security and Compatibility

- Treat project skills as workspace instructions and load them only in trusted workspaces. Referencing a script does not grant execution, network, or filesystem permission.
- Keep Markdown, scripts, icons, and other resources inside the skill root. Reject path traversal and escaping symlinks.
- Do not emit tokens, complete environments, authorization headers, or user data to stdout, logs, or eval results. Put structured results on stdout, diagnostics on stderr, and bound large output.
- Evaluation tooling must not inspect, copy, link, or reinterpret a user's Codex dotfiles, credentials, configuration, sessions, logs, or databases. Invoke the standard client and leave authentication ownership to it. Isolate conversation and workspace state rather than replacing the client's authentication state. Do not substitute an empty `CODEX_HOME` for model runs or claim that a CLI with an available ChatGPT login always needs an API key.
- Keep evaluation scripts portable and idempotent. The same fixtures and explicit inputs must produce the same selection, output schema, and filesystem effects on developer hosts and CI; never depend on incidental personal configuration.
- Separate portable Agent Skills rules from Codex extensions. `agents/openai.yaml` is not a universal package requirement.
- Prefer compatibility warnings for unknown fields or cosmetic differences. Block missing descriptions, unparseable YAML, invalid types, and unsafe resource boundaries.

---

## Evals Workflow

1. Give every skill at least eight positive and eight negative queries that exercise its real
   scope. Mix direct, indirect, embedded multi-step, informal, misspelled, and shared-keyword
   boundaries; do not add generic filler just to meet a count.
2. Keep a stable train/validation split. Change descriptions from training evidence only; do not paste failed queries or isolated keywords into routing text.
3. Validate datasets offline, check real Codex discovery, then run each routing query three times
   in separate ephemeral Codex CLI sessions with multi-agent disabled. Do not fork the current
   conversation or create subagents for routing measurements; require observable entrypoint
   evidence rather than self-reported usage.
4. Classify authentication, transport, timeout, missing completion, and unavailable evidence as `inconclusive`. Never count an inconclusive negative case as a routing success, and never tune a skill from infrastructure failures.
5. Use actual training-set false negatives and false positives to improve skill content. Broaden a description by intent category when positive cases miss; narrow adjacent boundaries when negative cases activate. Do not copy failed query wording or isolated keywords into the description.
6. After each meaningful train run, update the affected `description`, activation boundaries, workflow, or gotchas, then rerun train. A routing eval that produces findings but no justified skill review is incomplete.
7. Track precision, recall, specificity, false-positive rate, false-negative rate, per-query trigger rate, inconclusive trials, token/time cost, script use, constraint adherence, and final artifact quality. Treat cached input as part of reported input when the client reports it that way; do not add it again to total tokens.
   An early-stopped session can lack usage; treat token totals as lower bounds, not a cost estimate.
   For artifact-quality runs, use a fresh system temporary directory containing a synthetic fixture
   and a copy of the tested skill; do not give the agent a writable source checkout. Save only
   independently checked, redacted results back into the repository, separate from routing scores.
8. When training improvement plateaus, evaluate validation results. Revisit labels and query quality before adding more routing clauses, and do not tune further from held-out validation wording.
9. Add a separately held test set only when the dataset is large enough to preserve representative train and validation coverage. With small per-skill datasets, a third split creates unstable metrics; retain the fixed validation set and disclose that repeated iteration can still bias selection.

Exit the skill's constraints when the skill-authoring work is complete; do not apply them to later unrelated translation, copy, or business tasks.

---

## Evals Dataset Schema

Use one fixed format so every skill repository validates the same way:

```json
{
  "split": "train",
  "queries": [
    {
      "id": "skill-t01",
      "skill": "my-skill",
      "query": "...",
      "should_trigger": true,
      "category": "direct"
    }
  ]
}
```

- `split` is `"train"` or `"validation"`; the file declares itself instead of relying on its filename.
- `category` is one of `direct`, `indirect`, `embedded`, `boundary`:
  - `direct`: names the skill's domain explicitly.
  - `indirect`: describes a need without naming the domain.
  - `embedded`: hides the relevant task inside a larger multi-step request.
  - `boundary`: shares vocabulary but must not trigger.
- `category` and `should_trigger` are orthogonal: any category may be positive or negative. `boundary` usually maps to `should_trigger: false` because it is written as a near-miss, but that is a convention, not a schema requirement.
- Keep roughly 60/40 train/validation and at least eight positive and eight negative queries per
  skill.

---

## Routing Query Rules

- A positive query must be one the model cannot answer correctly without reading the skill. Anchor it on this repository's conventions, a repo-specific token, or a named script. Do not use general-knowledge questions, or the eval measures base-model self-discipline instead of routing.
- Negative queries must be near-misses: share the skill's keywords or concepts while requesting different work, and verify they stay untriggered.
- Do not combine implementation-style queries with an empty workspace. Make the query consultative, or provide a fixture project the agent can modify.

---

## Harness and Test Checklist

Routing evidence:

- Count a positive case only when the agent's own successful command output contains the target `SKILL.md` markers (`name: <skill>` and the level-one heading). Ignore self-reports, path mentions, failed commands, and partial output.
- Treat marker matching as a bounded routing heuristic, not proof of a filesystem read: a command
  could print both markers without opening the file. Document that limitation when reporting evals.
- Run a preflight first. Abort on hard failures (agent process failed, evaluation unavailable); retry transient failures (timeout, missing completion) before giving up.
- Tag failures with reason codes: `timeout`, `agent_process_failed`, `completion_event_missing`, `evaluation_unavailable`.
- Discover skills with a temporary empty `CODEX_HOME` and an allowlisted environment; run activation through the caller's normal Codex client and authentication.
- Write results incrementally and atomically (`.tmp` then rename) and record skills and dataset digests.

Tests to keep:

- Validator security paths: path traversal, escaping symlinks, invalid YAML, missing descriptions.
- Real script execution: idempotency, redaction, parameter handling.
- Harness semantics: evidence rules, deterministic sampling, preflight abort.

---

## Gotchas

- Keyword-only activation: add negative cases sharing the vocabulary and rewrite descriptions around user intent and boundaries.
- Over-fixed workflow: retain decision points and exit conditions instead of forcing every task through one sequence.
- Natural-language deterministic logic: move it into an idempotent, non-interactive script with `--help` and structured output.
- File-only validation: test discovery, routing, script execution, and important behavioral constraints separately.
- Zero-token exit: inspect unclosed quotes, accidental shell syntax, unusual `!` content, and host parsing boundaries.
- Stale facts: link authoritative sources, mark a version or applicability date, or query live
  status instead of writing short-lived facts as permanent rules.
- No maintenance strategy: mark version-sensitive facts and how to refresh them; prefer a linked
  source or a checking script over a hard-coded value that will silently rot.
- Rules that nag, stall execution, or complicate tool parameters: remove or simplify them; a rule
  that demands frequent reporting or blocks continuation without a decision rarely earns its
  context cost.

---

## Report

Report skill-authoring work in this order:

1. Routing scope and adjacent boundaries reviewed.
2. Changed skill resources and why each change affects agent decisions.
3. Validation and eval evidence, including model, actual Codex version, runner digest,
   dataset digest, and whether the result's skill digest matches the current tree. Report artifact
   acceptance separately from routing metrics and do not mark unrun samples as passed.
4. Remaining behavior, credential, platform, or held-out-data risks.

Apply this skill to itself once when changing its own rules: check its description, structure,
resources, eval guidance, and report format against the updated text. Stop after that fixed-point
pass; do not recursively repeat the same self-review without new changes or evidence.

---

## Validation

Run at least:

```bash
make validate
make eval
```

Also run the installed system `skill-creator/scripts/quick_validate.py` for each changed skill when available. That refers only to the script shipped with the system `skill-creator` skill in the current Codex installation, not a same-named script found online and not this repository's `scripts/packages/validate_skills.py`. Repository validation remains necessary because the two validators cover different contracts. Execute new scripts through important success and failure paths. Report changed resources, routing boundaries, structural and behavioral checks, metrics, and risks that still require a real client or credentials.

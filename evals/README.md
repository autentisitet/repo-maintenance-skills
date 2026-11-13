# Skill Evals

Repository index: [README](../README.md) — installation, the skill list, validation, and design
conventions.

The query set contains 100 train and 60 validation cases across ten skills (eight positive and
eight negative cases per skill). Use training evidence to revise descriptions; do not tune from
held-out query wording.

| Evidence | Scope |
| --- | --- |
| [README metrics and charts](../README.md#routing-metrics-historical) | Historical subset; three retired mirror queries excluded. Skill and dataset digests differ from the current tree. Not rerun due to model cost. |
| [Artifact acceptance samples](artifact_acceptance.md) | Output quality tasks for all ten skills; separate from routing. |
| [Artifact review template](artifact-reviews/TEMPLATE.md) | Blank report for independently checked, redacted results. |
| [Repo-hygiene review](artifact-reviews/2026-11-13-repo-hygiene.md) | One limited trial; nine skills have no behavior score. |

The replacement `github-repo-management` queries have not been model-evaluated. Do not describe
the historical metrics as measurements of the current query set.

## Query set formats

The canonical datasets are `train_queries.json` and `validation_queries.json`. Their top-level
object carries `version` (schema version) and `split_seed` (the random split seed) alongside
`split` and `queries`.

For Excel review and bulk editing, each JSON has a UTF-8 CSV sibling with a BOM and the columns
`id,skill,category,query,should_trigger`:

```bash
make csv-export   # regenerate the CSVs from the JSON files
make csv-import   # regenerate the JSON files from the CSVs, then validate
make csv-check    # verify JSON and CSV stay in sync (also part of make validate)
```

CSV export prefixes formula-like text (`=`, `+`, `-`, `@`, tab, or carriage return) with an
apostrophe so Excel treats it as text; import reverses only escapes emitted by the exporter.

When importing an edited CSV:

- The canonical JSON retains its top-level `version` and `split_seed` metadata.
- A same-directory temporary file replaces it atomically only if its SHA-256 has changed.
- `make validate` rejects JSON/CSV drift. Each model result records the evaluated JSON digest;
  Git tracks the source files, so no extra checksum manifest is maintained.

---

## Offline Validation

```bash
python3 -m scripts.evals.validate_skill_evals
```

This checks JSON shape, registered skills, duplicate cases, categories, label coverage, split
ratio, and obvious credential patterns. It does not call a model or establish routing quality.

---

## Codex Discovery

Check that Codex actually discovers the repository skills without a model call:

```bash
python3 -m scripts.evals.check_skill_discovery \
  --output evals/results/discovery.json
```

The checker creates an isolated temporary workspace and writable temporary `CODEX_HOME`, then verifies that each expected skill is enabled at repository scope and resolves to the intended source.

---

## Activation Evaluation

Each case runs three times by default in independent `codex exec --ephemeral --json` processes.

| Boundary | Runner behavior |
| --- | --- |
| Conversation | Fresh temporary workspace per trial; multi-agent and bundled skills disabled. No subagent route. |
| Authentication | The standard CLI uses its available ChatGPT sign-in or API key; model runs do not override `CODEX_HOME`. Only the no-model discovery checker creates an empty temporary `CODEX_HOME`. |
| Data | The repository does not inspect or copy credentials and does not persist raw model output or stderr. Queries are transmitted to the configured model. |

Run a low-cost smoke test with one positive and one negative case per skill:

```bash
make smoke
```

Equivalent direct invocation:

```bash
python3 -m scripts.evals.run_activation_evals evals/train_queries.json \
  --allow-model-calls --sample-per-label 1 \
  --runs 1 --jobs 1 --timeout 180 \
  --output evals/results/codex-smoke.json
```

`--allow-model-calls` explicitly authorizes model capacity and data transmission. Sessions use
read-only workspaces. The runner requests `shell_environment_policy.inherit="core"` but does not
verify which variables the installed Codex treats as core.

Activation evidence is a successful tool command naming `SKILL.md` whose output contains the
target skill's entrypoint markers. Self-reports, path-only mentions, failed commands, and partial
output do not count. This remains a heuristic: matching output does not prove a filesystem read.

| Operation | Behavior |
| --- | --- |
| Early stop | Once target markers appear, terminate the session: positive = pass, negative = fail. An absent read requires a completed turn. |
| Output cap | Retain up to 8,000 tokens of each tool output; cache entrypoint markers per runner invocation. |
| Timeout | Default 180 s; train/validation Make targets use 300 s. |
| Preflight | Run one trial first. On hard infrastructure failure, stop before other model calls and preserve any existing output. Retry timeouts and missing completion events once with extra time. |

---

## Incremental re-runs

Only runs with a pinned `--model` can reuse decided trials from the same `--output` path.

| Required match | Effect of a mismatch |
| --- | --- |
| Runner and skill digests | Re-evaluate all cases. Older results missing runner SHA cannot be reused. |
| Actual `codex --version` and pinned model | Re-evaluate all cases. |
| Each case's `query_sha256` and complete decided (pass/fail) trial count | Re-evaluate that case; never reuse an inconclusive trial. |

For a fully independent run, choose another output path. The canonical JSON dataset is hashed
after `make csv-import`; editing CSV alone does not alter evaluated inputs.

---

## SHA-256 provenance and storage

| Result field | Hashed input |
| --- | --- |
| `skills_sha256` | Sorted skill resource paths and bytes, excluding bytecode and caches. |
| `runner_sha256` | Evaluator and skill-discovery helper paths and bytes. |
| `dataset_sha256` | Canonical JSON bytes, not the CSV. |
| `query_sha256` (per row) | Canonical JSON of `id`, `skill`, `category`, `query`, and `should_trigger`. |

The runner stores these fields with model and Codex version under Git-ignored `evals/results/`.
Each update writes to a same-directory `.tmp` file before an atomic replace. `make metrics`
compares recorded skill, dataset, and runner digests with the current tree: `current` = match,
`stale` = mismatch, `unknown` = missing historical field. A changed dataset hash makes the
overall result stale even if unchanged individual cases remain reusable. Hash equality does not
measure task quality or imply the model was rerun.

The archived README charts live in `assets/evals/`; they were rendered from a filtered historical
subset, not from a new evaluation. `make plot-baseline` can regenerate them only when the ignored
historical raw result files are available locally.

---

## Retrying timeouts

Infrastructure-inconclusive trials (timeout, process failure, missing completion, unavailable
evaluation) carry no routing evidence. Extract just those cases into a small retry dataset and run
the normal runner against it; the original result file is left untouched so the retry stays
auditable:

```bash
make retry-set
python3 -m scripts.evals.run_activation_evals evals/results/retry-validation-queries.json \
  --allow-model-calls --runs 1 --jobs 1 --timeout 300 \
  --output evals/results/retry-validation.json
```

`make retry-set` defaults to `timeout` reasons; use the script directly with `--reason` and
`--min-trials` to control the filter. Merge the retry output back into the original result only
explicitly, and keep both files so the original and retried run stay distinguishable.

---

## Cross-model validation

To check whether an eval error is model-specific or query-specific, run the same dataset under
several models and compare per-case outcomes. Models are never hard-coded; pass them on the
command line:

```bash
python3 -m scripts.evals.cross_validate evals/validation_queries.json \
  --allow-model-calls \
  --model deepseek-flash --model gpt-6-luna \
  --output-dir evals/results
```

Each model runs once, serially, with a 300-second timeout. The first `--model` is the baseline;
each subsequent model is compared against it. The output is a
per-case outcome matrix plus `disappeared`/`introduced` error counts (FN, FP, timeout, process
failure, completion missing, unavailable). `make cross` is a shortcut using `CROSS_MODELS`
(default `deepseek-flash gpt-6-luna`). Use `--compare-only` to re-render the comparison from
existing per-model result files without spending model calls.

---

## Summarize and Plot

Derive routing metrics deterministically from one or more result files:

```bash
python3 -m scripts.evals.summarize_evals evals/results/activation-train.json
python3 -m scripts.evals.summarize_evals evals/results/activation-train.json --json
```

The summary separates three signals:

| Signal | Interpretation |
| --- | --- |
| Routing | Confusion counts, precision, recall, specificity, FPR, FNR, F1, accuracy, balanced accuracy; grouped by skill and query category. |
| Stability | Per-query trigger rates and disagreements across valid repeated trials. |
| Infrastructure | Inconclusive rate and reasons (`timeout`, `process_failed`, `completion_missing`, `unavailable`); these do not enter routing denominators. |

Use category failures to review routing boundaries: weak indirect/embedded recall may indicate
a too-literal description; boundary false positives may indicate overly broad scope. Older
results without categories appear under `unknown`. A stale digest describes an older snapshot,
not current performance.

ROC/AUC/P-R curves are deliberately not offered: a repeated-query trigger rate measures routing
stability, not a calibrated per-example model score. Treating its few discrete values as threshold
scores would fabricate a ranking signal. Loss and per-epoch curves are also inapplicable because
the repository iterates skill snapshots rather than optimizing model epochs.

Chart rendering is a separate module and uses matplotlib, which is a declared project dependency:

```bash
python3 -m scripts.evals.plot_evals \
  evals/results/activation-train.json evals/results/activation-validation.json \
  --output-dir evals/results
```

The plotter draws confusion counts, per-skill rates, query-trigger distributions and
inconclusive reasons. A single train/validation pair is a **comparison**, not an iteration
trend; multiple snapshots of one split form a trend. Undefined rates display `N/A`, not zero.
Split labels default to filenames; override with `--label` in file order. `make metrics` and
`make plot` run the corresponding summarize and plot commands after `make sync`.

`make plot-baseline` excludes three retired case IDs (`repo-t02`, `repo-t05`, `repo-v02`) and
copies the README charts to `assets/evals/`. It requires the locally saved raw results: a
fresh clone does not include Git-ignored `evals/results/`. `make plot` uses unfiltered data.

Supported charts:

- `{prefix}-confusion.png` — 2×3 routing confusion matrix (first result file)
- `{prefix}-per-skill.png` — per-skill precision/recall bars (first result file)
- `{prefix}-per-skill-errors.png` — per-skill FNR/FPR with decided and inconclusive counts
- `{prefix}-radar.png` — per-skill precision / recall / F1 radar charts (first result file)
- `{prefix}-inconclusive.png` — inconclusive trials by infrastructure reason (first result file)
- `{prefix}-trigger-rate.png` — positive/negative query trigger-rate distributions (first result file)
- `{prefix}-trend.png` — split comparison for one pair, or trends for multiple snapshots

Pass@1-vs-cost curves are not implemented.

---

## Interpretation

- Positive case: the target skill should be observed on every run.
- Negative case: the target skill should not be observed.
- Inconclusive: the run did not provide reliable evidence, for example because authentication, the agent process, or completion events failed. Do not count it as a negative success.
- The report includes pass, fail, and inconclusive counts, per-trial usage and duration, a dataset digest, a skill-package digest, and completed/expected progress.
- Routing success is not enough. Separately inspect whether an activated skill follows its important constraints, uses deterministic scripts correctly, and produces acceptable artifacts.
- Early stopping can end a session before `turn.completed` reports usage. Missing usage means unknown
  consumption, not zero tokens. Reported token totals are lower bounds, not actual model bills; do
  not assume independent sessions or subagents are cheaper without measured usage.
- Keep the train/validation split stable. If repeated tuning stops improving results, revisit labels and query quality before adding more routing text.

Metric definitions:

- **Session / trial / round**: one `codex exec --ephemeral` invocation; each query runs three by
  default.
- **Evidence**: a read counts only when a successful `command_execution` reads the target
  `SKILL.md` and its output contains the `name: <skill>` marker plus the level-one heading.
- **pass / fail / inconclusive**: pass = read matched `should_trigger`; fail = any reliable
  routing mismatch (false positive or false negative); inconclusive = infrastructure prevented
  reliable evidence. Infrastructure-inconclusive trials are excluded from
  P/R/FPR/FNR/specificity/F1/accuracy denominators. The summarizer still maps legacy runner
  non-infrastructure inconclusive positive misses to FN.
- **TP/TN/FP/FN**: TP = read on positive; TN = no read on negative; FP = read on negative;
  FN = positive completed without reading.
- **Rates**: P = TP/(TP+FP); R = TP/(TP+FN); specificity = TN/(TN+FP);
  F1 = harmonic mean of P and R;
  Acc = (TP+TN)/(TP+FN+FP+TN); FPR = FP/(FP+TN); FNR = FN/(FN+TP).
- **Inconclusive rate** = inconclusive / total trials, also split into positive-query and
  negative-query rates. **Coverage** = decided / total trials. **Pass rate** = pass / total
  trials.
- **Query trigger rate** = observed target-skill reads / valid trials for that query. Infrastructure
  failures do not enter the denominator. It is a stability diagnostic, not a calibrated model score.
- **Time** = per-session wall-clock (`duration_seconds` per trial), overall
  mean/median/P95/min/max and per-skill mean/P95. **Cost** = per-trial `usage` tokens plus
  **tokens per second** (output tokens / total session time). `reported_total_tokens` is input plus
  output; cached input is shown separately and is not added a second time. Early-stopped trials may
  have no usage, so totals are lower bounds. **Model** = the pinned `--model` slug recorded in the
  result payload.
- **Train-vs-validation gap** = ΔF1 = F1(train) − F1(validation), plus ΔPrecision, ΔRecall,
  ΔAccuracy, ΔSpecificity, and ΔInconclusiveRate.

An independent test set is appropriate once each skill has enough cases to keep all three splits
representative. The current 16 cases per skill are intentionally kept as train/validation only;
splitting them three ways would make per-skill metrics too sparse. Repeated selection against the
validation set can still bias results, so record skill snapshots and avoid tuning from individual
held-out wording.

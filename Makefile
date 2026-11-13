VENV_PYTHON := .venv/bin/python
PYTHON ?= $(shell if [ -x "$(VENV_PYTHON)" ]; then echo "$(VENV_PYTHON)"; else echo python3; fi)
DATASET ?= evals/train_queries.json
RUNS ?= 1
SAMPLE_PER_LABEL ?= 1
MODEL ?=
CROSS_MODELS ?= deepseek-flash gpt-6-luna

.DEFAULT_GOAL := usage

.PHONY: usage validate eval smoke eval-train eval-validation eval-full sync metrics plot plot-baseline csv-export csv-import csv-check retry-set cross install install-copy

usage:
	@printf '%s\n' \
	  'Repository maintenance skills:' \
	  '' \
	  'Offline:' \
	  '  make sync             create the uv environment' \
	  '  make validate         package, dataset, test, docs, and syntax checks' \
	  '  make eval             validate plus Codex discovery (no model call)' \
	  '  make metrics          summarize saved train and validation results' \
	  '  make plot             render charts from saved results' \
	  '  make plot-baseline    regenerate tracked historical README charts' \
	  '' \
	  'Model-backed:' \
	  '  make smoke MODEL=x              one positive and negative per skill' \
	  '  make eval-train MODEL=x         full training split, three runs each' \
	  '  make eval-validation MODEL=x    full validation split, three runs each' \
	  '  make eval-full MODEL=x          run both full splits' \
	  '  make cross CROSS_MODELS="a b"   compare validation across models' \
	  '  make retry-set                  extract timed-out cases' \
	  '' \
	  'Datasets:' \
	  '  make csv-export       JSON to Excel-friendly CSV' \
	  '  make csv-import       CSV to JSON, preserving metadata' \
	  '  make csv-check        verify JSON and CSV are in sync' \
	  '' \
	  'Installation:' \
	  '  make install          symlink skills into CODEX_HOME' \
	  '  make install-copy     copy skills into CODEX_HOME'

validate:
	@$(PYTHON) -m scripts.packages.validate_skills --strict
	@$(PYTHON) -m scripts.evals.validate_skill_evals
	@$(PYTHON) -m scripts.evals.convert_queries check evals/train_queries.json evals/train_queries.csv
	@$(PYTHON) -m scripts.evals.convert_queries check evals/validation_queries.json evals/validation_queries.csv
	@$(PYTHON) -m unittest discover -s tests -p 'test_*.py'
	@$(PYTHON) skills/markdown-docs/scripts/section-dividers.py --check .
	@bash -n scripts/links/install.sh skills/*/scripts/*.sh

eval: validate
	@$(PYTHON) -m scripts.evals.check_skill_discovery --output evals/results/discovery.json

smoke: eval
	@$(PYTHON) -m scripts.evals.run_activation_evals $(DATASET) \
	  --allow-model-calls --sample-per-label $(SAMPLE_PER_LABEL) \
	  --runs $(RUNS) --jobs 1 --timeout 180 $(if $(MODEL),--model $(MODEL),) \
	  --output evals/results/codex-smoke.json

eval-train: eval
	@$(PYTHON) -m scripts.evals.run_activation_evals evals/train_queries.json \
	  --allow-model-calls --runs 3 --jobs 2 --timeout 300 $(if $(MODEL),--model $(MODEL),) \
	  --output evals/results/activation-train.json

eval-validation: eval
	@$(PYTHON) -m scripts.evals.run_activation_evals evals/validation_queries.json \
	  --allow-model-calls --runs 3 --jobs 2 --timeout 300 $(if $(MODEL),--model $(MODEL),) \
	  --output evals/results/activation-validation.json

eval-full: eval-train eval-validation

sync:
	uv sync

metrics:
	@$(PYTHON) -m scripts.evals.summarize_evals \
	  evals/results/activation-train.json evals/results/activation-validation.json

plot:
	@$(PYTHON) -m scripts.evals.plot_evals \
	  evals/results/activation-train.json evals/results/activation-validation.json \
	  --output-dir evals/results

plot-baseline:
	@$(PYTHON) -m scripts.evals.plot_evals \
	  evals/results/activation-train.json evals/results/activation-validation.json \
	  --exclude-id repo-t02 --exclude-id repo-t05 --exclude-id repo-v02 \
	  --output-dir evals/results
	@cp evals/results/routing-confusion.png evals/results/routing-per-skill.png \
	  evals/results/routing-per-skill-errors.png evals/results/routing-radar.png \
	  evals/results/routing-trend.png assets/evals/

csv-export:
	@$(PYTHON) -m scripts.evals.convert_queries to-csv evals/train_queries.json evals/train_queries.csv
	@$(PYTHON) -m scripts.evals.convert_queries to-csv evals/validation_queries.json evals/validation_queries.csv

csv-import:
	@$(PYTHON) -m scripts.evals.convert_queries to-json evals/train_queries.csv evals/train_queries.json
	@$(PYTHON) -m scripts.evals.convert_queries to-json evals/validation_queries.csv evals/validation_queries.json
	@$(PYTHON) -m scripts.evals.validate_skill_evals

csv-check:
	@$(PYTHON) -m scripts.evals.convert_queries check evals/train_queries.json evals/train_queries.csv
	@$(PYTHON) -m scripts.evals.convert_queries check evals/validation_queries.json evals/validation_queries.csv

retry-set:
	@$(PYTHON) -m scripts.evals.extract_retry_queries \
	  evals/results/activation-train.json evals/train_queries.json \
	  evals/results/retry-train-queries.json
	@$(PYTHON) -m scripts.evals.extract_retry_queries \
	  evals/results/activation-validation.json evals/validation_queries.json \
	  evals/results/retry-validation-queries.json

cross:
	@$(PYTHON) -m scripts.evals.cross_validate evals/validation_queries.json \
	  --allow-model-calls \
	  $(foreach m,$(CROSS_MODELS),--model $(m)) \
	  --output-dir evals/results

install:
	@./scripts/links/install.sh

install-copy:
	@./scripts/links/install.sh --copy

---
name: project-layout
description: Use only when the user explicitly requests this repository's fixed directory convention or the existing project already follows it. Organize frontend, backend, deployment configuration, tests, scripts, integration examples, documentation, and machine-learning code. Do not use when preserving a framework-native layout or another architecture.
metadata:
  short-description: Organize application, deployment, tests, docs, and ML directories
---

# Project Layout

## Top-Level Responsibilities

| Directory | Responsibility |
| --- | --- |
| `frontend/` | Frontend source, assets, build configuration, frontend-only types |
| `deploy/` | Backend APIs, services, workers, and other server runtime code |
| `deploy-config/` | Nginx, Compose, process management, and deployment configuration |
| `tests/` | Unit, integration, end-to-end, migration, and security tests |
| `scripts/` | Repeatable environment, build, dataset, and model preparation tools |
| `examples/` | Local frontend/backend integration examples and sample inputs; do not commit concrete examples by default |
| `docs/` | Architecture, design notes, and generated backend documentation |
| `src/` | ML, data processing, training, evaluation, and inference core code |
| `train-config/` | Training, evaluation, and experiment configuration |

When a backend calls ML functionality, keep HTTP/service startup code in `deploy/` and model/training/inference logic in `src/`. Connect them through a clear module boundary; do not duplicate implementations.

---

## Internal Organization

Do not flatten `deploy-config/`. Create only the subdirectories the project uses, for example:

```text
deploy-config/
├── nginx/
├── compose/
├── systemd/
└── environments/
```

Keep Nginx sites, snippets, and certificate references grouped under `nginx/` by purpose. The container
project is the exception to the root-file rule: `.dockerignore` and `Dockerfile` stay at repository root,
Compose files live under `deploy-config/compose/`, and runtime-specific Docker/Podman, CPU/GPU, SELinux,
and logging rules use `$container-quality`. Non-secret per-environment differences may live under
`environments/`; never commit keys or real credentials.

Group tests by level or subsystem while keeping a recognizable relationship with source boundaries. Group
scripts by purpose such as `build/`, `data/`, `models/`, and `dev/`. Download scripts must verify origin,
checksums, and failure retries; do not commit datasets or model weights into the scripts directory.

Organize docs by type, for example architecture diagrams under `docs/architecture/` and generated FastAPI
OpenAPI under `docs/api/openapi.json`. Generated files are updated by the real application or tooling; do
not maintain a second handwritten copy.

---

## Integration Examples

Keep `examples/readme.md` with prerequisites, startup, data preparation, expected results, and cleanup. Ignore local examples while preserving that guide:

```gitignore
# Local frontend-backend integration examples
examples/*
!examples/readme.md
```

Do not rename it to `examples/`, or the later negation rule cannot re-include `readme.md`.

A single simple example may live directly under `examples/`. When there are multiple scenarios, multiple
backends or frontend entrypoints, or one example with several files, use scenario subdirectories such as
`examples/login-flow/` and `examples/upload-flow/` instead of flattening every request, response, script,
and sample into the root.

Before packaging or sharing examples, remove usernames, email addresses, hosts, IPs, tokens, tenants,
internal project names, real business IDs, and equivalent sensitive values, using neutral names such as
`user-a.json` and `server-local.txt`. Strip the same information from file contents and metadata; renaming
a file does not make it safe.

---

## Moving an Existing Project

- Search imports, build contexts, CI path filters, container COPY instructions, Nginx references, test fixtures, and documentation before moving files; update every reference afterward without leaving compatibility symlinks or duplicate copies that mask problems.
- Use version-control-aware moves and keep business refactoring separate from layout migration.
- Do not create `.gitkeep`. When an empty runtime directory must exist, use an internal `.gitignore` with the comment on its own line.
- Do not create every top-level directory mechanically. Add a directory only when its responsibility exists.

---

## Verification

- Run existing builds, tests, type checks, and packaging, and confirm imports, working directories, and build contexts work after the move.
- Inspect version-control state for leaked examples, datasets, model weights, secrets, or duplicate old files.
- For FastAPI projects, confirm `docs/api/openapi.json` was regenerated from the moved application object.
- Report moved directories, updated references, and checks not run. A tidy-looking directory tree does not prove the application still builds or deploys.

---
name: backend-quality
description: Use when a project explicitly adopts this repository's FastAPI, Nginx, and Docker/Podman backend conventions and the task changes or reviews APIs, generated OpenAPI, file uploads, database migrations, automated tests, or backend code quality. Do not use for serverless systems, managed gateways, other public-entry architectures, or ordinary backends that do not adopt this deployment model.
metadata:
  short-description: Review APIs, uploads, OpenAPI, migrations, Nginx, and tests
---

# Backend Quality

## Code Quality

- Follow established project lint, formatting, typing, and naming conventions (Python prefers PEP 8, with type annotations per project convention); do not introduce a parallel style system.
- Use readable names that accurately describe their purpose and only established unambiguous abbreviations. Avoid single-letter variables, vague names, and inconsistent spelling.
- Keep functions focused. Document non-obvious intent, preconditions, side effects, parameters, results, and failure modes for complex or abstract-API functions; do not mechanically comment self-explanatory code.
- Explain "why" in comments; do not restate "what" the code does line by line.

---

## API Contract

- When routes, request/response models, status codes, or authentication change, update tests, callers, documentation, and machine-readable contracts together.
- Generate `docs/api/openapi.json` from the real FastAPI application object. Do not edit it manually or maintain a disconnected schema.
- Confirm that the result parses, then review paths, methods, schemas, required fields, security, and responses. Parsing does not prove behavior.
- Keep operation IDs stable and unique. Identify removals, renames, narrowed types, and status changes as compatibility risks.

Example generation pattern:

```bash
python - <<'PY'
import json
from pathlib import Path
from app.main import app

target = Path("docs/api/openapi.json")
temporary = target.with_suffix(".json.tmp")
target.parent.mkdir(parents=True, exist_ok=True)
temporary.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
temporary.replace(target)
PY
python -m json.tool docs/api/openapi.json >/dev/null
```

If importing the application connects to production services, runs migrations, or has other side effects, fix the initialization boundary before generating the contract. Never use production credentials merely to obtain the file.

---

## Public Entry Point

- Use Nginx as the only public HTTP/HTTPS entry point. Do not expose Uvicorn, Gunicorn, or another application server directly to the internet. Local development is exempt.
- Bind application servers to loopback, a Unix socket, or a controlled private address. Limit firewall, security-group, and container publishing to the Nginx path.
- Configure TLS termination, routing, body limits, timeouts, and necessary rate limits in Nginx.
- Trust forwarded headers only from known proxy addresses and constrain host, client-address, and protocol headers to prevent arbitrary clients from spoofing proxy information.
- Disable reload and debug modes in production and use explicit health, shutdown, and process-management behavior.

---

## File Uploads

- Enforce explicit size limits in both Nginx and the application. Count streamed bytes and stop immediately on overflow; do not trust `Content-Length` alone.
- Validate content with an allowlist, magic bytes, and a real parser where applicable. Do not trust MIME headers, extensions, or original filenames. Reject uploads whose declared type, extension, and actual content disagree.
- Generate opaque server-side names with at least 128 bits of cryptographic randomness. Derive extensions only from verified types. At most, keep the original filename as length-limited, sanitized display metadata; never use it to build filesystem paths.
- Normalize every final path and confirm that it remains inside the storage root. Apply the same rule to every archive member; reject `../`, absolute paths, drive letters, and equivalent encodings.
- Never execute uploads. Store them outside the web root with non-executable permissions and do not pass upload paths to shells, interpreters, templates, or dynamic loaders. Perform conversion, extraction, or scanning in a resource-constrained isolated process.

---

## Data and Migrations

- Do not expose Redis or databases publicly. Use `$container-quality` for network, port, and rootless-container details.
- Use controlled tunnels, VPNs, bastions, or loopback forwarding for operations; isolation does not replace authentication, least privilege, or encryption.
- Apply schema changes through reviewable, repeatable migrations, not implicit startup mutation.
- Plan rollback or forward recovery, lock duration, compatibility windows, backups, and production-scale rehearsal for risky transformations.
- Define transaction boundaries explicitly. Avoid external calls inside long transactions. Retry only replay-safe operations or use idempotency and deduplication.

---

## Verification

- Cover success, validation failure, authentication/authorization failure, not-found, and key conflict paths.
- Test constraints, rollback, migrations, and external dependency failures with integration coverage. Do not mock away core persistence behavior.
- After changing a FastAPI API, generate the OpenAPI schema once in tests and compare it with the committed `docs/api/openapi.json` to prevent stale contract artifacts.
- For deployment changes, at least validate Nginx syntax and verify the health check and one representative API through the public entry path. A successful direct connection to the application port does not prove the public proxy chain is correct.

---

## Report

Report API compatibility, whether `docs/api/openapi.json` is updated, the unit/integration/migration/Nginx checks performed, and remaining production risks. Do not describe schema generation success, passing syntax checks, or test-double success as end-to-end proof.

---
name: container-quality
description: "Use when creating, modifying, or reviewing Docker/Podman Compose deployments that adopt this repository's fixed conventions: one root Dockerfile, one base topology, Docker/Podman CPU/GPU overrides, Ubuntu/Fedora SELinux compatibility, and log rotation. Do not use for Kubernetes, managed cloud orchestration, or projects that do not adopt this layout."
metadata:
  short-description: Standardize Docker/Podman builds, overrides, SELinux, and logs
---

# Container Quality

## Invariants

- Docker and Podman share the root `.dockerignore` and `Dockerfile`; do not maintain engine-specific Dockerfiles.
- `deploy-config/compose/docker-compose.yaml` is the only complete topology. Define services, networks, named volumes, health checks, and common logging there.
- Keep runtime and accelerator differences in exactly four overrides: `docker-compose.docker-cpu.yaml`, `docker-compose.docker-gpu.yaml`, `docker-compose.podman-cpu.yaml`, and `docker-compose.podman-gpu.yaml`.
- Default to CPU. Select GPU only when the user explicitly enables it and the host has the required runtime, drivers, and hardware.
- Do not publish Redis, databases, or other internal services to public host interfaces; connect them only to the Compose internal network.

---

## References

| Task | Reference |
| --- | --- |
| Layout, base topology, merge behavior, Makefile commands | [compose.md](references/compose.md) |
| Docker/Podman, Ubuntu/Fedora, rootless, SELinux, GPU | [platforms.md](references/platforms.md) |
| Log rotation, build security, runtime validation | [logging-security.md](references/logging-security.md) |

Load only the references required by the current task.

---

## Workflow

1. Confirm that the project adopts this fixed layout, then inspect the runtime, Compose frontend, distribution, SELinux state, and CPU/GPU requirement.
2. Change service topology only in the base file, then verify that all four overrides still match service names and mounts.
3. Resolve every affected base-plus-override combination. One successful combination does not prove the others.
4. When possible, build and start the target combination and inspect health, internal networking, mount permissions, shutdown, and log rotation.

---

## Report

Report the runtime, Compose frontend, distribution, SELinux state, CPU/GPU combinations, log rotation, and untested combinations. `compose config` proves only basic parsing and merge behavior, not image builds, startup, GPU access, or actual rotation.

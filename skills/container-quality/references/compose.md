# Compose Layout and Commands

## Fixed Layout

```text
project-root/
├── .dockerignore
├── Dockerfile
└── deploy-config/
    └── compose/
        ├── docker-compose.yaml
        ├── docker-compose.docker-cpu.yaml
        ├── docker-compose.podman-cpu.yaml
        ├── docker-compose.docker-gpu.yaml
        └── docker-compose.podman-gpu.yaml
```

Do not place Compose files at repository root or directly under `deploy-config/`. Do not maintain competing `compose.yaml`, `docker-compose.yml`, or per-service entrypoints.

---

## Base and Override Files

The base file defines every service, network, named volume, health check, dependency, and common logging option. Add, remove, or rename services there, then update the four overrides only when their runtime-specific differences require it.

An override must contain only runtime or accelerator differences. It must not duplicate the full service list or change unrelated images, ports, networks, or business configuration. Always combine the base file with exactly one override; never stack CPU and GPU overrides together.

---

## Makefile Selection

Select one Compose frontend, then derive the runtime from that command. Independent detection can mix Docker commands with Podman overrides on hosts that install both.

```makefile
COMPOSE := $(shell \
	if command -v podman >/dev/null 2>&1 \
		&& command -v podman-compose >/dev/null 2>&1; then \
		echo "podman-compose"; \
	elif command -v podman >/dev/null 2>&1 \
		&& podman compose version >/dev/null 2>&1; then \
		echo "podman compose"; \
	elif command -v docker >/dev/null 2>&1 \
		&& command -v docker-compose >/dev/null 2>&1; then \
		echo "docker-compose"; \
	elif command -v docker >/dev/null 2>&1 \
		&& docker compose version >/dev/null 2>&1; then \
		echo "docker compose"; \
	else \
		echo ""; \
	fi)

RUNTIME := $(if $(filter podman%,$(COMPOSE)),podman,$(if $(filter docker%,$(COMPOSE)),docker,))

COMPOSE_DIR := deploy-config/compose
COMPOSE_FILES := -f $(COMPOSE_DIR)/docker-compose.yaml

GPU ?= 0
GPU_DISABLED := $(filter 0 false no,$(strip $(GPU)))

ifeq ($(RUNTIME),podman)
ifneq ($(GPU_DISABLED),)
COMPOSE_FILES += -f $(COMPOSE_DIR)/docker-compose.podman-cpu.yaml
else
COMPOSE_FILES += -f $(COMPOSE_DIR)/docker-compose.podman-gpu.yaml
endif
endif

ifeq ($(RUNTIME),docker)
ifneq ($(GPU_DISABLED),)
COMPOSE_FILES += -f $(COMPOSE_DIR)/docker-compose.docker-cpu.yaml
else
COMPOSE_FILES += -f $(COMPOSE_DIR)/docker-compose.docker-gpu.yaml
endif
endif

COMPOSE_CMD = $(COMPOSE) $(COMPOSE_FILES)
```

Container targets must reject empty `COMPOSE` or `RUNTIME`, then use `COMPOSE_CMD` for `build`, `up`, `down`, `logs`, and `config`. Command-line overrides should set only `COMPOSE` so `RUNTIME` remains derived.

---

## Combination Validation

```bash
docker compose -f deploy-config/compose/docker-compose.yaml -f deploy-config/compose/docker-compose.docker-cpu.yaml config
docker compose -f deploy-config/compose/docker-compose.yaml -f deploy-config/compose/docker-compose.docker-gpu.yaml config
podman compose -f deploy-config/compose/docker-compose.yaml -f deploy-config/compose/docker-compose.podman-cpu.yaml config
podman compose -f deploy-config/compose/docker-compose.yaml -f deploy-config/compose/docker-compose.podman-gpu.yaml config
```

All merged combinations must contain the same service set. Differences should be limited to intended runtime, rootless, or GPU settings.

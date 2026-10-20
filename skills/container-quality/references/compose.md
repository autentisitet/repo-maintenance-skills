# Compose 布局与命令

## 固定布局

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

Compose 文件不得平铺到仓库根目录或 `deploy-config/` 根部。不要同时维护 `compose.yaml`、
`docker-compose.yml` 或按单个服务拆出的多套入口文件。

---

## 基础文件与覆盖文件

`docker-compose.yaml` 集中声明全部服务、网络、命名卷、健康检查、依赖关系和通用 logging。新增、删除
或重命名服务时只修改基础文件，再检查四个覆盖文件是否仍需调整。

覆盖文件只表达对应引擎和加速模式的差异，不得复制完整服务清单，也不得改变无关服务的镜像、端口、
网络或业务配置。使用时始终组合基础文件和一个覆盖文件，不能同时叠加 CPU 与 GPU 覆盖。

---

## Makefile 命令一致性

Makefile 可以先选择可用 Compose 前端，再从命令推导容器引擎。不要独立探测 `COMPOSE` 和 `RUNTIME`，
否则机器同时安装 Docker 与 Podman 时可能混用命令和覆盖文件。

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

容器目标先确认 `$(COMPOSE)` 和 `$(RUNTIME)` 非空，再通过 `$(COMPOSE_CMD)` 执行 `build`、`up`、
`down`、`logs` 和 `config`。命令行覆盖时只覆盖 `COMPOSE`，让 `RUNTIME` 继续从它推导。

---

## 组合校验

```bash
docker compose -f deploy-config/compose/docker-compose.yaml -f deploy-config/compose/docker-compose.docker-cpu.yaml config
docker compose -f deploy-config/compose/docker-compose.yaml -f deploy-config/compose/docker-compose.docker-gpu.yaml config
podman compose -f deploy-config/compose/docker-compose.yaml -f deploy-config/compose/docker-compose.podman-cpu.yaml config
podman compose -f deploy-config/compose/docker-compose.yaml -f deploy-config/compose/docker-compose.podman-gpu.yaml config
```

检查四个合并结果包含相同服务集合，差异只来自预期的引擎、rootless 或 GPU 设置。

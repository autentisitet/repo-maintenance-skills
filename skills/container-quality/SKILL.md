---
name: container-quality
description: 创建、修改或审查采用本仓库约定的 Docker/Podman Compose 部署时使用，统一根目录 Dockerfile、单一服务拓扑、Docker/Podman 与 CPU/GPU 覆盖、Ubuntu/Fedora SELinux 兼容和日志轮转。不用于 Kubernetes、云平台托管编排或未采用该固定布局的项目。
metadata:
  short-description: 统一 Docker/Podman 构建、Compose 覆盖、SELinux 与日志轮转
---

# 容器质量

## 固定不变量

- Docker 和 Podman 共用仓库根目录的 `.dockerignore` 与 `Dockerfile`，不维护 `Containerfile` 或引擎
  专用 Dockerfile。
- `deploy-config/compose/docker-compose.yaml` 是唯一完整服务拓扑；所有服务、网络、命名卷、健康检查
  和通用 logging 都在其中维护。
- Docker/Podman 与 CPU/GPU 的差异只放在四个覆盖文件中：
  `docker-compose.docker-cpu.yaml`、`docker-compose.docker-gpu.yaml`、
  `docker-compose.podman-cpu.yaml`、`docker-compose.podman-gpu.yaml`。
- 默认选择 CPU。只有用户明确启用 GPU 且目标环境具备 runtime、驱动和硬件时才使用 GPU 覆盖。
- Redis、数据库和其他内部服务不发布公网端口，只连接 Compose 内部网络。

---

## 按任务加载

| 任务 | Reference |
| --- | --- |
| 文件布局、基础拓扑、覆盖合并、Makefile 命令 | [compose.md](references/compose.md) |
| Docker/Podman、Ubuntu/Fedora、rootless、SELinux、GPU | [platforms.md](references/platforms.md) |
| 日志落盘轮转、构建安全和运行验证 | [logging-security.md](references/logging-security.md) |

只读取当前任务需要的 reference。修改跨越多个主题时再组合加载，不把所有细节默认塞进上下文。

---

## 共用流程

1. 先确认项目明确采用本仓库固定布局，并检查现有引擎、Compose 前端、目标发行版、SELinux 状态和
   CPU/GPU 需求。
2. 修改服务拓扑时只编辑基础 `docker-compose.yaml`，然后审查四个覆盖文件是否仍与服务名和挂载一致。
3. 分别解析受影响的基础文件与覆盖文件组合；不能因为一个组合成功就推断其他引擎或 GPU 组合可用。
4. 条件允许时实际构建并启动目标组合，检查服务健康、内部网络、挂载权限、停止行为和日志轮转。

---

## 交付

报告实际验证的容器引擎、Compose 前端、发行版、SELinux 状态、CPU/GPU 组合、日志轮转和未覆盖项。
Compose `config` 成功只能证明合并与语法基本有效，不能证明镜像可构建、容器可启动、GPU 可用或日志
已经真实轮转。

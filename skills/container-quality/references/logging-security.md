# 日志与构建安全

## 日志落盘与轮转

所有长期运行服务都把 stdout/stderr 交给可落盘且支持轮转的容器日志驱动。基础
`docker-compose.yaml` 定义共享 logging 配置，并让每个服务显式继承：

```yaml
x-logging: &default-logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "5"

services:
  api:
    logging: *default-logging
```

`max-size` 和 `max-file` 根据日志量与磁盘预算调整，但不得无限增长。应用自身写文件日志时也要轮转，
且不要与容器 stdout 无控制地重复记录同一内容。

Docker 与 Podman 可能使用不同底层日志实现。部署前检查合并配置和实际容器日志驱动，并产生足以超过
`max-size` 的非敏感测试日志，确认日志真实落盘、轮转且磁盘占用受限。

---

## 构建上下文

- Docker 和 Podman 都从仓库根目录构建，例如 `docker build -f Dockerfile .` 和
  `podman build -f Dockerfile .`。
- `.dockerignore` 排除密钥、版本控制元数据、本地环境、数据集、模型权重、测试输出和无关构建产物。
- Dockerfile 不先复制整个仓库再删除敏感内容；先限制上下文，再按构建阶段只复制必需文件。

---

## 密钥与权限

- 不把密码、token、私钥或真实环境文件写进 Dockerfile、Compose、镜像层或 build args。使用运行时
  secret 机制或受控外部注入。
- 不用 `--privileged` 掩盖设备、挂载或权限配置错误。只授予服务实际需要的 capability、设备和目录。
- 检查镜像构建记录和 Compose 合并结果，确认敏感值没有进入可提交文件或镜像历史。

# 容器平台兼容

## Ubuntu 与 Fedora

- 自动化脚本先识别发行版和可用包管理器，不假定只有 `apt` 或只有 `dnf`。
- Docker 使用 `docker compose`，Podman 使用 `podman compose` 或明确探测到的 `podman-compose`；不要
  通过 shell alias 假装两个引擎完全等价。
- 在 Ubuntu 检查 AppArmor、文件所有者和 rootless 路径；在 Fedora 以 SELinux Enforcing 模式检查
  标签、UID/GID 映射、Unix socket 和设备访问。

---

## SELinux 与挂载

- 优先使用命名卷。必须绑定宿主机目录时，私有数据使用 `:Z`，确实需要多个容器共享时使用 `:z`。
- 权限失败时先检查 SELinux 标签、容器用户、rootless UID/GID 映射和挂载选项。
- 不通过关闭 SELinux、使用 `--privileged` 或无边界递归修改目录权限解决挂载问题。
- 临时运维访问通过受控隧道或仅绑定 loopback 的转发，不为数据库和 Redis 增加公网端口。

---

## CPU 与 GPU

- CPU 是默认模式，不依赖 GPU runtime 或设备声明。
- Docker GPU 和 Podman GPU 的设备、runtime、CDI 或 hook 差异分别留在各自覆盖文件，不假设两者语法
  与主机配置完全相同。
- 只有目标主机具备对应硬件、驱动和容器集成时才验证 GPU 组合；没有 GPU 时明确报告未覆盖，不用
  结构校验替代设备行为。

---

## 运行验证

分别用目标引擎构建根目录 `Dockerfile`。条件允许时至少在 Ubuntu 和 Fedora Enforcing 各启动一种
CPU 组合；检查健康状态、内部网络隔离、绑定挂载、rootless 权限、重启行为和停止时的数据完整性。

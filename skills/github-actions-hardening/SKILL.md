---
name: github-actions-hardening
description: 编写或修改 GitHub Actions 工作流、Dependabot 配置、CodeQL 设置，以及调试 CI 日志输出时使用。覆盖 runner 差异、权限最小化、第三方 Action 的可信性、密钥泄露与日志体积问题。不适用于本地构建脚本或非 GitHub 的 CI 平台。
metadata:
  short-description: 审查 workflow 权限、依赖安全、密钥使用和 CI 日志输出
---

# GitHub Actions

| 任务 | Reference |
| --- | --- |
| 写或修改 `.github/workflows/*.yml` | [ci.md](references/ci.md) |
| Dependabot、CodeQL | [ci.md](references/ci.md#依赖与安全扫描) |
| 日志脱敏、压缩、高亮、分组 | [log-hygiene.md](references/log-hygiene.md) |

## 默认检查项

- `permissions:` 显式声明。顶层给最小集合（通常 `contents: read`），需要写权限的 job 单独提升。
- 对可被新提交取代的验证任务，配置 `concurrency:` + `cancel-in-progress: true`。发布、迁移和其他必须完整执行的任务不要照搬。
- 按风险选择 Action 引用：只读校验流程中的 GitHub 官方 Action 可以使用 major tag；第三方 Action，或接触 secrets、写权限、OIDC、发布与部署的流程，优先固定完整 commit SHA。
- 跨平台 job 若共享 Bash 脚本，显式设置 `shell: bash`；依赖 PowerShell 或平台原生 shell 的任务保留对应 shell。
- 对可能挂起、调用外部服务或运行时间明显受输入影响的 job，建议设置合理的 `timeout-minutes`。

---

## 写之前先确认

- 这个 job 是否需要 `pull_request` 之外的触发器？`pull_request_target` 在目标分支上下文运行，权限和 secrets 风险需要单独审查，不能直接执行不受信任的 PR 代码。
- 有没有把 CI 需要的文件写进了 `.gitignore` 或 `paths-ignore`？这类错误会让测试静默不跑。
- 工作流名与 badge、README 链接里引用的文件名一致吗？

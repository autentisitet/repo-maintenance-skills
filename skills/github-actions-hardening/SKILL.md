---
name: github-actions-hardening
description: 编写或修改 GitHub Actions 工作流、dependabot 配置、CodeQL 设置，以及调试 CI 日志输出时使用。覆盖 runner 差异、权限最小化、第三方 Action 的可信性、密钥泄露与日志体积问题。不适用于本地构建脚本或非 GitHub 的 CI 平台。
metadata:
  short-description: workflow、依赖扫描与 CI 日志的加固规范
---

# GitHub Actions

| 任务 | Reference |
| --- | --- |
| 写或修改 `.github/workflows/*.yml` | [ci.md](references/ci.md) |
| dependabot、CodeQL | [ci.md](references/ci.md#依赖与安全扫描) |
| 日志脱敏、压缩、高亮、分组 | [log-hygiene.md](references/log-hygiene.md) |

## 每个 workflow 都要有

- `permissions:` 显式声明。顶层给最小集合（通常 `contents: read`），需要写权限的 job 单独提升。
- `concurrency:` + `cancel-in-progress: true`。同一个分支连续推送时，旧任务应该被取消而不是排队。
- 第三方 Action 固定到 commit SHA。浮动 tag 由作者控制，可以被重新指向别的提交。
- `defaults.run.shell: bash`。Windows runner 默认是 pwsh，同一份脚本会在那里失败。
- `timeout-minutes:`。默认 6 小时，卡死时浪费额度。

## 写之前先确认

- 这个 job 是否需要 `pull_request` 之外的触发器？`pull_request_target` 会带着目标分支的权限运行并暴露 secrets。
- 有没有把 CI 需要的文件写进了 `.gitignore` 或 `paths-ignore`？这类错误会让测试静默不跑。
- 工作流名与 badge、README 链接里引用的文件名一致吗？

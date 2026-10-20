---
name: github-repo-management
description: 规划仓库分支名、分批提交和测试，或创建、克隆、迁移、重命名和调整 GitHub 仓库设置时使用，包括 license、About 与 topics。默认只读，远程写操作先展示命令和影响；不负责业务代码实现或 PR 内容审查。
metadata:
  short-description: 规划分支、提交与测试，并管理 GitHub 仓库设置和展示元数据
---

# GitHub 仓库管理

先判断任务属于哪一类，只加载对应 reference。

| 任务 | Reference |
| --- | --- |
| 推荐 branch、分批 commit、message 和测试命令 | [commit-planning.md](references/commit-planning.md) |
| 平台之间迁移 git 历史 | [mirror-migration.md](references/mirror-migration.md) |
| visibility、rename、license、About、topics、homepage | [repository-settings.md](references/repository-settings.md) |

## 远程写操作

执行 `git push`、`gh repo create/edit/rename/delete` 或写 GitHub API 前：

1. 先只读确认 `OWNER/REPO`、当前状态和影响。
2. 至少展示完整命令和目标；如果存在不可逆影响或可行的回滚方式，一并说明。
3. 仅通过 Codex 原生命令审批执行；对话文字不替代审批。
4. 审批不可用或被拒绝时停止，不换命令或工具绕过。
5. 执行后用只读命令验证结果。

迁移或较复杂的远程操作建议先运行 `<skill-dir>/scripts/preflight.sh`。如果迁移第三方仓库，还必须核对
许可证和 attribution；改为 private 不代表取得再分发权。

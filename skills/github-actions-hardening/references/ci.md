# Workflow 配置

## 最小骨架

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

defaults:
  run:
    shell: bash

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7
      - run: ./scripts/build.sh
```

---

## Action 引用策略

不要把 SHA pinning 当成所有 workflow 的固定格式。先看 Action 来源、job 权限和被篡改后的后果：

| 场景 | 建议引用方式 |
| --- | --- |
| GitHub 官方 Action；只读权限；不接触 secrets；只跑测试或静态检查 | major tag，例如 `actions/checkout@v7` |
| 第三方 Action，但 job 无 secrets 和写权限，输出也不作为可信发布物 | major tag 或完整 SHA，按仓库维护成本选择 |
| Action 接触 secrets、`contents: write`、`id-token: write`、发布、签名或部署 | 优先使用完整 commit SHA，并在旁边注明对应版本；若保留官方 Action 的 major tag，明确这是对发布方的信任选择 |

major tag 可能被维护者更新指向，完整 SHA 则牺牲更新便利换取不可变引用。选择应与实际权限和供应链风险匹配，不要让低风险校验仓库承担无收益的维护成本。

---

## paths-ignore

只在任务确实与这些文件无关时才忽略。忽略 `**/*.md` 之前先确认没有 markdown 校验步骤——否则校验永远不会触发，看起来一直绿。

```yaml
on:
  push:
    paths-ignore:
      - "docs/**"
      - "LICENSE"
```

注意 `paths-ignore` 与 `paths` 不能同时出现在同一个触发事件下。

---

## 权限

- 顶层写 `permissions: { contents: read }`，按 job 提升。
- `pull_request_target` 以目标分支权限运行，且能读取 secrets；fork 的 PR 代码若在其中被执行，等于把仓库交出去。除非明确需要，改用 `pull_request`。
- 发布类 job 需要 `contents: write` 时，只给那一个 job，不要整体提升。
- `id-token: write` 只在用 OIDC 换取云厂商凭证时开启。

---

## 密钥

详见 [log-hygiene.md](log-hygiene.md)。避免输出 secret；原值通常能被日志遮蔽，但编码、截断、拼接等派生值需要在输出前用 `::add-mask::` 单独登记。

---

## 矩阵

- `fail-fast: false` 只在需要一次看完全部失败项时开，否则会拖长反馈时间。
- 矩阵里每个组合都要有明确目的；把版本号全列一遍通常只是在浪费额度。
- `include` / `exclude` 写在矩阵内，不要用脚本拼 `matrix`。

---

## 缓存

- 依赖缓存的 key 通常应包含锁文件哈希，例如 `${{ hashFiles('**/uv.lock') }}`，并包含影响缓存兼容性的运行时和平台信息。
- 构建结果只有在输入和工具链都能可靠纳入 key 时才适合缓存；无法定义失效条件时优先缓存下载产物。

---

## 依赖与安全扫描

### Dependabot

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      actions:
        patterns: ["*"]
```

- 为仓库实际使用、且希望自动更新的生态配置 Dependabot；本 skill 涉及的仓库通常应包含 `github-actions`。
- 用 `groups` 合并 patch 更新，否则每个小版本都会单独开 PR。
- 使用 major tag 时让 Dependabot 提醒跨 major 升级；使用完整 SHA 时，审查更新是否对应可信 release，不要只看自动生成的版本注释。

### CodeQL

- 公开仓库优先用 Settings → Code security 里的 default setup，不要手写 workflow。
- 私有仓库是否能使用 CodeQL 取决于当前 GitHub 方案和安全功能配置；先检查仓库设置，再决定使用 default setup 或 workflow。
- 手写时 `permissions` 至少需要 `security-events: write`。

---

## 常见失败

| 现象 | 原因 |
| --- | --- |
| Windows job 脚本报语法错 | 默认 shell 是 pwsh，没设 `shell: bash` |
| 缓存一直不更新 | key 里没有锁文件哈希 |
| PR 的 secrets 为空 | fork PR 拿不到 secrets，这是预期行为 |
| badge 显示 no status | 引用的 workflow 文件名或分支不存在 |

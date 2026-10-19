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
      - uses: actions/checkout@<commit-sha>  # 不要用浮动 tag
      - run: ./scripts/build.sh
```

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

## 权限

- 顶层写 `permissions: { contents: read }`，按 job 提升。
- `pull_request_target` 以目标分支权限运行，且能读取 secrets；fork 的 PR 代码若在其中被执行，等于把仓库交出去。除非明确需要，改用 `pull_request`。
- 发布类 job 需要 `contents: write` 时，只给那一个 job，不要整体提升。
- `id-token: write` 只在用 OIDC 换取云厂商凭证时开启。

## 密钥

详见 [log-hygiene.md](log-hygiene.md)。核心一条：`${{ secrets.X }}` 在使用处直接展开，先赋给中间变量会让脱敏失效。

## 矩阵

- `fail-fast: false` 只在需要一次看完全部失败项时开，否则会拖长反馈时间。
- 矩阵里每个组合都要有明确目的；把版本号全列一遍通常只是在浪费额度。
- `include` / `exclude` 写在矩阵内，不要用脚本拼 `matrix`。

## 缓存

- key 必须包含依赖文件的哈希：`${{ hashFiles('**/uv.lock') }}`。否则锁文件更新后仍然命中旧缓存，问题会以"本地能跑"的形式出现。
- 缓存的是下载产物，不要缓存构建结果——构建结果的失效条件很难写对。

## 依赖与安全扫描

### dependabot

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

- 至少配置 `github-actions` 生态；有 Python 依赖时加 `pip` 或 `uv`。
- 用 `groups` 合并 patch 更新，否则每个小版本都会单独开 PR。
- 与 SHA pinning 冲突：启用 pinning 后仍需人工确认 SHA 变更来自可信提交。

### CodeQL

- public repo 优先用 Settings → Code security 里的 default setup，不要手写 workflow。
- private repo 若未启用 GitHub Advanced Security，才需要自行编写 workflow，并确认 `language` 矩阵覆盖实际使用的语言。
- 手写时 `permissions` 至少需要 `security-events: write`。

## 常见失败

| 现象 | 原因 |
| --- | --- |
| Windows job 脚本报语法错 | 默认 shell 是 pwsh，没设 `shell: bash` |
| 缓存一直不更新 | key 里没有锁文件哈希 |
| PR 的 secrets 为空 | fork PR 拿不到 secrets，这是预期行为 |
| badge 显示 no status | 引用的 workflow 文件名或分支不存在 |

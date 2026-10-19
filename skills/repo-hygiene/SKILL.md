---
name: repo-hygiene
description: 新建仓库或整理通用配置文件时使用，包括 .gitignore、.gitattributes、.editorconfig、.dockerignore，以及 Python 项目的 requirements 导出与锁文件同步。不涉及业务代码的编写。
metadata:
  short-description: 仓库配置、忽略规则与依赖同步
---

# 仓库卫生

## 基础配置

每个仓库都应有 `.gitattributes` 和 `.editorconfig`。模板：

| 文件 | 模板 | 作用 |
| --- | --- | --- |
| `.editorconfig` | [assets/editorconfig](assets/editorconfig) | 缩进、换行、末尾空行 |
| `.gitattributes` | [assets/gitattributes](assets/gitattributes) | 换行归一、二进制标记、语言统计 |
| `.gitignore` | [assets/gitignore](assets/gitignore) | IDE、agent、构建产物基线 |

复制时去掉 `assets/` 前缀的模板名，改成以点开头的真实文件名。

`.dockerignore` 不要软链到 `.gitignore`：两者语义不同，镜像里可能反而需要被 git 忽略的文件（反之亦然）。

## `.gitignore` 要点

- 忽略 IDE 与 agent 的本地目录：`.idea/`、`.vscode/`（团队共享配置时只忽略 `*.code-workspace`）、`.claude/`、`.codex/`、`.agents/`。
- 只忽略本地状态。不要忽略 CI 要读的文件（`.github/`、锁文件、`requirements.txt`）。
- 环境变量：忽略 `.env` 与 `.env.*`，但保留 `!.env.example`。否定规则必须写在忽略规则之后，否则不生效。
- 构建产物按目录忽略（`dist/`、`build/`、`node_modules/`），不要用 `*.out` 这类过宽的规则。

## Python

### requirements.txt

不使用 uv 的用户需要 `requirements.txt`。它应由锁文件导出，不要手写：

```bash
uv export --no-hashes --format requirements-txt -o requirements.txt
```

旧版本 uv 等价于 `uv pip compile pyproject.toml -o requirements.txt`。

### 三处同步

仓库改名或版本变化时，以下必须一起改：

| 位置 | 怎么改 |
| --- | --- |
| `pyproject.toml` 的 `[project] version` | 手动改 |
| `uv.lock` | `uv lock` 重新生成 |
| `requirements.txt` | 重新导出 |

不要靠记忆同步。加一个检查，CI 里跑：

```bash
uv lock --check
uv export --no-hashes --format requirements-txt -o - | diff -u requirements.txt -
```

### 提交范围

`uv.lock` 要提交；`.venv/`、`__pycache__/`、`*.egg-info/`、`.pytest_cache/`、`.ruff_cache/` 不提交。

---
name: repo-hygiene
description: 新建仓库或整理通用配置文件时使用，包括 .gitignore、.gitattributes、.editorconfig、.dockerignore，以及 Python 项目的 requirements 导出与锁文件同步。不涉及业务代码的编写。
metadata:
  short-description: 审查仓库配置、忽略规则、换行策略与 Python 依赖同步
---

# 仓库卫生

## 基础配置

当仓库需要跨编辑器格式一致性或跨平台换行归一时，考虑加入 `.editorconfig` 和 `.gitattributes`。单文件实验、生成仓库或已有等价工具约束的项目不必机械添加。模板：

| 文件 | 模板 | 作用 |
| --- | --- | --- |
| `.editorconfig` | [assets/editorconfig](assets/editorconfig) | 缩进、换行、末尾空行 |
| `.gitattributes` | [assets/gitattributes](assets/gitattributes) | 换行归一、二进制标记、语言统计 |
| `.gitignore` | [assets/gitignore](assets/gitignore) | OS、环境变量、构建产物基线；IDE/agent 规则按需启用 |

复制时去掉 `assets/` 前缀的模板名，改成以点开头的真实文件名。

`.dockerignore` 不要软链到 `.gitignore`：两者语义不同，镜像里可能反而需要被 git 忽略的文件（反之亦然）。

---

## `.gitignore` 要点

- 只忽略确定不共享的 IDE 与 agent 本地状态。`.idea/`、`.vscode/`、`.claude/`、`.codex/`、`.agents/` 中可能包含团队配置，先检查仓库约定再添加规则。
- 只忽略本地状态。不要忽略 CI 要读的文件（`.github/`、锁文件、`requirements.txt`）。
- 环境变量：忽略 `.env` 与 `.env.*`，但保留 `!.env.example`。否定规则必须写在忽略规则之后，否则不生效。
- 构建产物按目录忽略（`dist/`、`build/`、`node_modules/`），不要用 `*.out` 这类过宽的规则。
- 不创建 `.gitkeep`。需要保留运行时或生成目录时，在该目录放置 `.gitignore`，忽略目录内容并显式
  保留 `.gitignore` 自身，例如：

  ```gitignore
  *
  !.gitignore
  ```

---

## Dotfile 注释

dotfile 中的说明性注释单独成行，放在对应配置项之前。不要把注释追加在配置值或忽略规则末尾；
某些格式不支持行尾注释，独立注释也更便于复制、排序和脚本化修改。

---

## Python

### requirements.txt

只有部署平台、下游工具或用户工作流明确需要 `requirements.txt` 时才维护它。使用 uv 的项目应从锁定结果导出，不要手写：

```bash
uv export --no-hashes --format requirements-txt -o requirements.txt
```

不要把 `uv pip compile pyproject.toml` 当成从 `uv.lock` 导出的等价操作；两者输入来源不同。

### 生成文件同步

采用 `pyproject.toml`、`uv.lock` 和导出型 `requirements.txt` 的项目，在依赖声明变化后同步生成文件：

| 位置 | 怎么改 |
| --- | --- |
| `pyproject.toml` | 修改直接依赖或约束 |
| `uv.lock` | 用 `uv lock` 重新解析 |
| `requirements.txt` | 从锁定结果重新导出 |

需要持续维护导出文件时，在 CI 中检查它没有过期：

```bash
uv lock --check
uv export --no-hashes --format requirements-txt -o - | diff -u requirements.txt -
```

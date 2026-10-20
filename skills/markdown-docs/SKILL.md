---
name: markdown-docs
description: 撰写或修改仓库内的 Markdown 文档时使用，包括 README、CHANGELOG、CONTRIBUTING、issue 模板、SECURITY、DISCLAIMER。确保 GitHub 实际渲染正确，并符合仓库的 markdownlint 配置。不适用于代码注释或非仓库的临时笔记。
metadata:
  short-description: 编写和审查仓库 README、CHANGELOG 与社区文档
---

# Markdown 文档

先判断文档类型，只加载对应 reference。三类文档都要遵守下面的共用约束。

| 文档 | Reference |
| --- | --- |
| README / README_zh、badge、目录、公式、图表、logo | [readme.md](references/readme.md) |
| CHANGELOG | [changelog.md](references/changelog.md) |
| issue 模板、CONTRIBUTING、SECURITY、DISCLAIMER、LICENSE | [community.md](references/community.md) |

## 共用约束

1. 先确认目标渲染环境。GitHub 与编辑器预览在 HTML 白名单、mermaid 版本、锚点生成上可能不同；涉及这些特性时查看实际渲染结果。
2. 仓库已有 markdownlint 配置或 CI 检查时遵守它。用户决定新引入 markdownlint 时，可从 [assets/markdownlint.json](assets/markdownlint.json) 开始调整。
3. 规则确实妨碍表达时，在配置中显式调整并说明原因，不要靠无意义的空行或拆句规避检查。
4. 重命名或新增文档后，同步检查 README 的目录和相对链接。
5. 同一 Markdown 文件存在多个二级标题时，在相邻二级章节之间放置独占一行的 `---` 水平分割线，
   分割线前后各保留一个空行。不要在第一个二级标题前机械添加，也不要修改代码围栏中的示例。

批量整理文档时先定位已安装的 skill 目录：

```bash
skill_dir="${CODEX_HOME:-$HOME/.codex}/skills/markdown-docs"
python3 "$skill_dir/scripts/section-dividers.py" .
python3 "$skill_dir/scripts/section-dividers.py" --check .
```

---

## 语言

- 中文正文用全角标点；中英文之间加空格；代码、路径、命令保持原样。
- 一句话说完的事不要拆成三点。列表只用于并列项。

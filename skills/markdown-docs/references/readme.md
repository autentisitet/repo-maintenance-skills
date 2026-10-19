# README

## 内容顺序

项目是什么 → 解决什么问题 → 怎么用 → 原理或架构 → 已知限制。

- 技术术语优先采用相关领域教材、标准或权威文档中的通行译法，同一概念全文保持一致。
- 让目标读者能快速判断项目做什么、适用场景和开始使用的方法。
- 不要用 CHANGELOG 的语气。避免"不再支持 xxx"这类以变更为中心的句子——读者想知道的是现在能做什么。
- 文档较长、章节较多时增加目录，并实际检查二级、三级标题锚点。

## 双语

仓库决定维护 `README.md` 与 `README_zh.md` 时：

- 顶部互相跳转：`[English](README.md) | [中文](README_zh.md)`。
- 章节顺序、代码块、表格、badge 保持一致；改一侧就同步另一侧。
- 双语不同步比只有单语更糟：读者会把过时的那一版当成现状。

## Badge

只添加能帮助读者判断项目状态、且链接真实存在的 badge。例如：

```markdown
[![version](https://img.shields.io/github/v/release/OWNER/REPO)](https://github.com/OWNER/REPO/releases)
[![ci](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/release.yml?label=release)](https://github.com/OWNER/REPO/actions/workflows/release.yml)
```

添加前确认 badge 指向的 release、workflow 和默认分支真实存在；无法长期维护的 badge 不要添加。

## 公式

- 行内用 `$...$`，独立公式用 `$$...$$`。
- GitHub 原生渲染 LaTeX；VS Code 需要 Markdown+Math 一类扩展。提交前在 GitHub 上看一眼，确认没有把 `$` 渲染成字面量（常见于货币符号或转义缺失）。

## 图表

- 架构与数据流适合用 mermaid 表达；图过密时拆图或改用更适合的独立文档。
- 渲染后检查尺寸与配色，确认读者第一眼落在重点上，而不是所有节点同等权重。
- mermaid.live 与 GitHub 部署的版本可能不同；提交前以目标平台的实际渲染为准。

## 性能数据

推理耗时、内存占用这类关键数字：

- 仓库里要有可复现的测量脚本，README 只引用结果。
- 交代统计口径：预热次数、重复次数、取中位数还是 p95、硬件与驱动版本、输入规模。
- 给出公式，例如吞吐 = batch_size / 单步耗时。

## Logo

优先使用清晰、可访问且许可证明确的资产。矢量 logo 可用 `.svg` 引用；照片或复杂纹理使用适当的位图格式。需要居中时可用 GitHub 支持的写法：

```html
<p align="center"><img src="assets/logo.svg" width="160" alt="logo"></p>
```

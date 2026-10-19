# README

## 内容顺序

项目是什么 → 解决什么问题 → 怎么用 → 原理或架构 → 已知限制。

- 术语使用计算机各课程（计算机网络、操作系统、计算机组成原理、数据结构与算法、数据库、机器学习、深度学习）的标准译法，同一概念全文只用一个词。
- 至少说清三件事：有什么功能、在什么场景有用、用户怎么用。
- 不要用 CHANGELOG 的语气。避免"不再支持 xxx"这类以变更为中心的句子——读者想知道的是现在能做什么。
- 必须有目录，锚点能跳到二级、三级标题。

## 双语

`README.md` 与 `README_zh.md`：

- 顶部互相跳转：`[English](README.md) | [中文](README_zh.md)`。
- 章节顺序、代码块、表格、badge 保持一致；改一侧就同步另一侧。
- 双语不同步比只有单语更糟：读者会把过时的那一版当成现状。

## Badge

至少 version、ci、release 三个：

```markdown
[![version](https://img.shields.io/github/v/release/OWNER/REPO)](https://github.com/OWNER/REPO/releases)
[![ci](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/release.yml?label=release)](https://github.com/OWNER/REPO/actions/workflows/release.yml)
```

badge 指向的工作流必须真实存在；否则 GitHub 只显示 "no status"，比没有 badge 更糟。

## 公式

- 行内用 `$...$`，独立公式用 `$$...$$`。
- GitHub 原生渲染 LaTeX；VS Code 需要 Markdown+Math 一类扩展。提交前在 GitHub 上看一眼，确认没有把 `$` 渲染成字面量（常见于货币符号或转义缺失）。

## 图表

- 架构与数据流用 mermaid。节点超过约 15 个时改用独立 HTML，否则在 README 宽度下会缩成一团。
- 渲染后检查尺寸与配色，确认读者第一眼落在重点上，而不是所有节点同等权重。
- GitHub 的 mermaid 版本落后于 mermaid.live，避免使用新语法。

## 性能数据

推理耗时、内存占用这类关键数字：

- 仓库里要有可复现的测量脚本，README 只引用结果。
- 交代统计口径：预热次数、重复次数、取中位数还是 p95、硬件与驱动版本、输入规模。
- 给出公式，例如吞吐 = batch_size / 单步耗时。

## Logo

用 `.svg` 内联或作为图片引用，不要用位图。需要居中时用 GitHub 支持的写法：

```html
<p align="center"><img src="assets/logo.svg" width="160" alt="logo"></p>
```

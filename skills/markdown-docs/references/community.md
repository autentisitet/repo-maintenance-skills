# 社区文档

## `.github/ISSUE_TEMPLATE/*.md`

模板较长或容易让贡献者误以为所有字段必填时，可在开头说明它只是辅助结构：

> This is a suggested template, not a mandatory reporting format. Use the
> sections that help communicate the problem; a clear free-form request is welcome.

模板里的字段要能直接回答问题；"描述你的问题"这种空标题没有信息量。

## `.github/CONTRIBUTING.md`

- 语气平等、欢迎，假设读者是第一次贡献，但不需要手把手教 git。
- 根据项目实际工作流组织环境、开发、检查、提交和问题报告，不固定标题或顺序。
- 可执行步骤给出仓库中真实存在的命令；不要写无法落地的“安装依赖”“运行检查”。
- 说明提交前要跑哪些检查，以及失败了怎么定位。

## `SECURITY.md`

说明受支持版本，例如：

```text
Security fixes are targeted at the latest version on the default branch. Older
releases may not receive fixes.
```

同时给出私下报告渠道（邮箱或 GitHub Security Advisories），不要要求用户开公开 issue 描述漏洞。

## `DISCLAIMER.md`

- 免责声明涉及法律效果时优先让有资质的人审核。维护多语言版本时明确哪一版为准并保持同步。
- 默认使用清楚、现代的书面英语。正式法律语域中，可以使用约定俗成且含义更精确的拉丁词源术语；不要仅因词源而用生僻长词替换更清楚的盎格鲁-撒克逊词源词汇。
- 判断标准是法律含义、适用范围和读者能否准确理解，而不是词源本身。无法用普通词完整表达的术语，在首次出现时解释。
- 明确适用范围（软件、数据、模型输出）和责任边界，不要写成长篇法律文本。

## `LICENSE`

- 修改或分发他人代码时遵守上游许可证，并在 README 注明来源与改动范围。
- 仓库同时分发第三方资产（字体、图标、模型权重、数据集）时，逐个核对许可证，不要只看代码的。
- 更换许可证前核对现有许可证、贡献协议和各贡献者授权；无法确认再许可权利时不要擅自改。

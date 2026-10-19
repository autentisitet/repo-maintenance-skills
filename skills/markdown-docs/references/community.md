# 社区文档

## `.github/ISSUE_TEMPLATE/*.md`

`bug_report.md`、`feature_request.md` 开头加一句，降低用户对格式的焦虑：

> This is a suggested template, not a mandatory reporting format. Use the
> sections that help communicate the problem; a clear free-form request is welcome.

模板里的字段要能直接回答问题；"描述你的问题"这种空标题没有信息量。

## `.github/CONTRIBUTING.md`

- 语气平等、欢迎，假设读者是第一次贡献，但不需要手把手教 git。
- 二级标题顺序：

1. Environment Setup
2. Coding Standards
3. Development Workflow
4. Dependencies
5. Security and CI
6. Reporting Issues
7. Contribution Checklist

- 每一步给出可直接执行的命令。"安装依赖"这类没有命令的步骤等于没写。
- 说明提交前要跑哪些检查，以及失败了怎么定位。

## `SECURITY.md`

至少包含：

```text
Security fixes are targeted at the latest version on the default branch. Older
releases may not receive fixes.
```

同时给出私下报告渠道（邮箱或 GitHub Security Advisories），不要要求用户开公开 issue 描述漏洞。

## `DISCLAIMER.md`

- 只写英文，不维护中文版本——免责声明出现两个版本时，歧义会成为问题。
- 用词精确、书面化，避免含糊的日常表达；能选更准确的词时优先选它。
- 明确适用范围（软件、数据、模型输出）和责任边界，不要写成长篇法律文本。

## `LICENSE`

- 修改或分发他人代码时遵守上游许可证，并在 README 注明来源与改动范围。
- 仓库同时分发第三方资产（字体、图标、模型权重、数据集）时，逐个核对许可证，不要只看代码的。
- 更换许可证需要所有贡献者同意；历史贡献没有明确授权时不要擅自改。

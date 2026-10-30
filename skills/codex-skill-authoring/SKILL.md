---
name: codex-skill-authoring
description: 创建、审查或精简本仓库的 Codex skill 时使用，包括判断是否值得新增、设计 description 与渐进披露结构、维护 agents/openai.yaml，以及验证 references、scripts 和 assets。不用于安装第三方 skill 或编写普通项目文档。
metadata:
  short-description: 创建、审查和精简 Codex skill，并验证结构、路由与上下文成本
---

# Codex Skill 编写

## 先判断是否需要

- 先检查现有 skill，避免能力重叠或新增过薄的 skill。
- 只写会改变 Codex 决策、补充项目约定或约束真实风险的内容。基础命令教程、通用编程常识和
  Codex 默认就能完成的推理通常不写。
- 个人反复使用的工作流、术语和偏好可以直接写成约束，不必为了适合其他用户而泛化。涉及特定
  工具版本或时效性事实时，说明适用条件，方便以后更新。
- 更新现有 skill 时优先删除无效规则和重复说明，不因个别案例不断追加绝对规则。

---

## 组织内容

- skill 目录和 frontmatter `name` 使用相同的 lowercase kebab-case 名称。
- `description` 说明实际能力、触发场景和必要边界；不要把完整工作流塞进 description。
- `SKILL.md` 只保留共用约束和路由。只有存在多个实质场景时才拆分 `references/`。
- 重复执行且需要确定性的操作可放入 `scripts/`；会进入最终交付物的模板或素材放入 `assets/`。
- 不创建没有明确用途的 README、CHANGELOG、空目录或示例占位文件。

---

## 措辞

- “必须/不要”只用于正确性、安全边界或用户明确要求。
- “至少”用于最低交付或最低检查范围。
- “建议/推荐/通常”用于经验性做法和可选优化。
- 规则只在特定任务下适用时，使用“如果/当……时/按需”，不要暗示该操作一定发生。
- 示例用于澄清非显然行为，不用于重复 Codex 已知的基础语法。

---

## UI 元数据

如果提供 `agents/openai.yaml`：

- `display_name`、`short_description` 和 `default_prompt` 与 `SKILL.md` 的定位一致。
- `default_prompt` 显式引用 `$<skill-name>`。
- 保持默认自动匹配；只有用户明确要求显式调用时才设置
  `policy.allow_implicit_invocation: false`。
- 修改已有文件时保留无关的 `policy`、`dependencies` 和其他字段。

---

## 验证

至少运行：

```bash
python3 scripts/validate_skills.py
python3 scripts/test_validate_skills.py
python3 scripts/test_skill_examples.py
python3 skills/markdown-docs/scripts/section-dividers.py --check .
bash -n scripts/install.sh skills/*/scripts/*.sh
```

这里的“官方 `quick_validate.py`”特指当前 Codex 安装中随系统 `skill-creator` skill 提供的
`scripts/quick_validate.py`，不指网络上搜索到的同名脚本，也不指本仓库的
`scripts/validate_skills.py`。如果该脚本在当前环境可读且可运行，用它逐个验证新增或修改的 skill；
仓库校验器仍要运行，因为两者检查范围不同。新增脚本时实际运行其关键路径；复杂或高风险 skill
在条件允许时补充独立行为验证。最后报告修改文件、验证结果和仍未覆盖的风险，不把结构校验描述成
行为正确性证明。

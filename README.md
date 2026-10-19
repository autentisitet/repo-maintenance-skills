# codex-skills

个人维护的 Codex 自定义 skills。只面向 Codex，不保证在其他 agent 上可用。

## 安装

```bash
git clone <repo-url> ~/codex-skills
cd ~/codex-skills
./scripts/install.sh
```

`install.sh` 把 `skills/*` 软链到 `${CODEX_HOME:-~/.codex}/skills`。
Windows 下没有符号链接权限时用 `./scripts/install.sh --copy`，之后改动需要重新执行。

安装后在 Codex 里用 `$markdown-docs` 这样的名字显式调用，也可以由 description 自动匹配。

## Skills

| Skill | 用途 |
| --- | --- |
| [markdown-docs](skills/markdown-docs/SKILL.md) | README、CHANGELOG、CONTRIBUTING、issue 模板等仓库文档 |
| [github-actions-hardening](skills/github-actions-hardening/SKILL.md) | workflow 配置、dependabot、CodeQL、CI 日志 |
| [repo-hygiene](skills/repo-hygiene/SKILL.md) | dotfiles、忽略规则、依赖导出与锁文件同步 |
| [frontend-quality](skills/frontend-quality/SKILL.md) | HTML/CSS 取值收敛、渲染验证、可访问性 |

## 结构

```text
codex-skills/
├── scripts/
│   ├── install.sh          # 安装到 CODEX_HOME
│   └── validate_skills.py  # 结构和链接校验，CI 也跑这个
└── skills/
    └── <skill-name>/
        ├── SKILL.md        # 必需：frontmatter + 路由 + 共用约束
        ├── agents/
        │   └── openai.yaml # 可选：UI 名称、调用策略
        ├── references/     # 可选：按场景加载的细节
        ├── scripts/        # 可选：可执行助手
        └── assets/         # 可选：模板、配置片段
```

## 新增 skill

1. 建目录：`mkdir -p skills/<name>`
2. 写 `SKILL.md`，frontmatter 必须有 `name`（与目录同名）和 `description`
3. 校验：

   ```bash
   python3 scripts/validate_skills.py
   ```

## 设计约定

- **SKILL.md 只做路由。** 细节放 `references/`，按场景只读需要的那一份。
- **只写改变决策的信息。** “要兼容主流浏览器”这类常识不写。
- **能脚本化的就脚本化。** 校验命令、模板生成优先做成 `scripts/`，不要靠文字描述。
- **不写绝对化的偏好。** 个人审美标注为可选，不要写成通用规则。
- **控制数量。** 每个 skill 的 name + description 都会常驻上下文，四个精的胜过十个薄的。

## 调用策略

默认允许自动匹配。若某个 skill 希望只能显式调用，在 `agents/openai.yaml` 加：

```yaml
policy:
  allow_implicit_invocation: false
```

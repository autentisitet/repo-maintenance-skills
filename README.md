# repo-maintenance-skills

一组面向仓库维护工作的 Codex skills，覆盖文档、GitHub Actions、仓库配置和前端质量检查。

这是社区维护的非官方项目，与 OpenAI 不存在隶属或背书关系。内容只针对 Codex 的 skill
格式进行验证，不承诺兼容其他 agent。

## 安装

### macOS、Linux 与 WSL

```bash
git clone https://github.com/autentisitet/repo-maintenance-skills.git ~/repo-maintenance-skills
cd ~/repo-maintenance-skills
./scripts/install.sh
```

脚本把 `skills/*` 软链接到 `${CODEX_HOME:-~/.codex}/skills`。需要复制而不是链接时：

```bash
./scripts/install.sh --copy
```

复制安装不会自动跟随仓库更新。需要刷新已安装副本时，显式执行
`./scripts/install.sh --copy --force`。`--force` 只替换与本仓库同名的 skill，使用前应确认
目标目录中没有需要保留的本地修改。

### Windows PowerShell

```powershell
git clone https://github.com/autentisitet/repo-maintenance-skills.git "$HOME\repo-maintenance-skills"
Set-Location "$HOME\repo-maintenance-skills"
.\scripts\install.ps1
```

PowerShell 安装器默认创建目录 junction，不需要启用开发者模式或获取符号链接权限。需要独立副本时使用
`.\scripts\install.ps1 -Copy`；刷新已有副本时使用 `-Copy -Force`。

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
repo-maintenance-skills/
├── scripts/
│   ├── install.sh          # macOS、Linux 与 WSL
│   ├── install.ps1         # Windows PowerShell
│   └── validate_skills.py  # 结构和链接校验
└── skills/
    └── <skill-name>/
        ├── SKILL.md        # 必需：frontmatter + 路由 + 共用约束
        ├── agents/
        │   └── openai.yaml # 可选：UI 名称、调用策略
        ├── references/     # 可选：按场景加载的细节
        ├── scripts/        # 可选：可执行助手
        └── assets/         # 可选：模板、配置片段
```

## 校验

```bash
python3 scripts/validate_skills.py
bash -n scripts/install.sh skills/*/scripts/*.sh
```

校验器检查 frontmatter、目录命名、内部链接和 `agents/openai.yaml` 的默认提示词。它只能验证
结构，不代表 skill 中的技术判断必然正确；涉及安全、版本和平台行为的内容仍需对照一手文档。

## 新增 skill

1. 建目录：`mkdir -p skills/<name>`
2. 写 `SKILL.md`，frontmatter 必须有 `name`（与目录同名）和 `description`
3. 运行校验：

   ```bash
   python3 scripts/validate_skills.py
   ```

## 设计约定

- **SKILL.md 保持精简。** 只有存在多个实质场景时才做路由，条件性细节放 `references/`。
- **只写改变决策的信息。** “要兼容主流浏览器”这类常识不写。
- **能脚本化的就脚本化。** 校验命令、模板生成优先做成 `scripts/`，不要靠文字描述。
- **不写绝对化的偏好。** 个人审美标注为可选，不要写成通用规则。
- **控制数量。** 每个 skill 的 name + description 都会常驻上下文，四个精的胜过十个薄的。

本项目采用 [MIT License](LICENSE)。

## 调用策略

默认允许自动匹配。若某个 skill 希望只能显式调用，在 `agents/openai.yaml` 加：

```yaml
policy:
  allow_implicit_invocation: false
```

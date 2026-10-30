# repo-maintenance-skills

[English](README.md) | [中文](README_zh.md)

一组面向 Codex 的仓库维护 skills，将常用工程约定整理成可复用的操作流程，覆盖文档、GitHub
Actions、仓库配置、项目目录、前后端质量以及 Docker/Podman 部署。

项目优先服务作者的实际工作流，部分目录、部署和工具选择属于明确的项目约定，不作为适合所有仓库的
通用最佳实践。这是非官方项目，与 OpenAI 不存在隶属或背书关系，也不承诺兼容 Codex 之外的 agent。

## Skills

| Skill | 用途 |
| --- | --- |
| [codex-skill-authoring](skills/codex-skill-authoring/SKILL.md) | 创建、审查和精简 Codex skill |
| [markdown-docs](skills/markdown-docs/SKILL.md) | README、CHANGELOG、CONTRIBUTING、issue 模板等仓库文档 |
| [github-actions-hardening](skills/github-actions-hardening/SKILL.md) | workflow、Dependabot、CodeQL 和 CI 日志 |
| [github-repo-management](skills/github-repo-management/SKILL.md) | branch、分批 commit、测试建议和 GitHub 仓库管理 |
| [repo-hygiene](skills/repo-hygiene/SKILL.md) | dotfiles、忽略规则、依赖导出和锁文件同步 |
| [project-layout](skills/project-layout/SKILL.md) | 组织前后端、部署配置、测试、脚本、示例、文档和训练代码目录 |
| [container-quality](skills/container-quality/SKILL.md) | Docker/Podman 共用构建、Compose 覆盖、SELinux 和日志轮转 |
| [backend-quality](skills/backend-quality/SKILL.md) | 后端接口契约、FastAPI OpenAPI、迁移、测试、代码规范和 Nginx 公网入口 |
| [frontend-quality](skills/frontend-quality/SKILL.md) | HTML/CSS 取值收敛、渲染验证和可访问性 |

安装后可以用诸如 `$markdown-docs` 这类名称显式调用，也可以由 description 自动匹配。

---

## 安装

### macOS、Linux 与 WSL

```bash
git clone https://github.com/autentisitet/repo-maintenance-skills.git ~/repo-maintenance-skills
cd ~/repo-maintenance-skills
./scripts/install.sh
```

默认把 `skills/*` 软链接到 `${CODEX_HOME:-~/.codex}/skills`。需要独立副本时使用：

```bash
./scripts/install.sh --copy
```

### Windows PowerShell

```powershell
git clone https://github.com/autentisitet/repo-maintenance-skills.git "$HOME\repo-maintenance-skills"
Set-Location "$HOME\repo-maintenance-skills"
.\scripts\install.ps1
```

默认创建目录 junction；需要独立副本时使用 `.\scripts\install.ps1 -Copy`。

`--force` / `-Force` 只替换指向当前仓库的链接或带本项目安装标记的复制副本。遇到来源未知的同名
目录时会停止，避免删除用户自行维护的 skill。

---

## 更新

软链接或 junction 安装时，拉取仓库更新即可生效：

```bash
git pull
```

复制安装需要重新覆盖对应副本：

```bash
./scripts/install.sh --copy --force
```

Windows 使用 `.\scripts\install.ps1 -Copy -Force`。只有本项目创建的链接或带安装标记的复制副本
会被替换。

---

## 结构

```text
repo-maintenance-skills/
├── requirements.txt
├── scripts/
│   ├── install.sh
│   ├── install.ps1
│   ├── test_skill_examples.py
│   ├── test_validate_skills.py
│   └── validate_skills.py
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        ├── scripts/
        └── assets/
```

除 `SKILL.md` 外的目录按需创建，不保留空目录或占位文件。

---

## 校验

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate_skills.py
python3 scripts/test_validate_skills.py
python3 scripts/test_skill_examples.py
python3 skills/markdown-docs/scripts/section-dividers.py --check .
bash -n scripts/install.sh skills/*/scripts/*.sh
```

校验器使用真实 YAML 解析检查 frontmatter、目录命名、内部链接和 `agents/openai.yaml`。

新增或修改 skill 时可以调用 `$codex-skill-authoring`，再运行以上校验。

---

## 设计约定

- **个人工作流优先。** 个人的重复需求、术语和偏好可以直接成为约束，不为追求通用性而改写。
- **只写会改变决策的信息。** 不重复 Codex 已有的基础能力和通用教程。
- **按需拆分。** `SKILL.md` 保留共用约束，条件性细节放进 `references/`，确定性操作放进
  `scripts/`。
- **措辞与约束强度一致。** 安全和正确性要求使用“必须/不要”，最低范围使用“至少”，经验性做法
  使用“建议/推荐/通常”，条件任务使用“如果/当……时”。
- **控制上下文成本。** 少量有实际增益的 skill 比大量薄 skill 更有价值。

---

## License

本项目采用 [MIT License](LICENSE)。

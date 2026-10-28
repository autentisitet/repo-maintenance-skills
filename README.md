# repo-maintenance-skills

[English](README.md) | [中文](README_zh.md)

A set of Codex repo-maintenance skills that turn common engineering conventions into reusable
workflows, covering documentation, GitHub Actions, repository configuration, project layout,
frontend/backend quality, and Docker/Podman deployment.

The project prioritizes the author's actual workflows. Some directory, deployment, and tool choices
are explicit project conventions rather than general best practices suitable for every repository.
This is an unofficial project with no affiliation with or endorsement by OpenAI, and it does not
promise compatibility with agents other than Codex.

## Skills

| Skill | Purpose |
| --- | --- |
| [codex-skill-authoring](skills/codex-skill-authoring/SKILL.md) | Create, review, and simplify Codex skills |
| [markdown-docs](skills/markdown-docs/SKILL.md) | Repository docs such as README, CHANGELOG, CONTRIBUTING, and issue templates |
| [github-actions-hardening](skills/github-actions-hardening/SKILL.md) | Workflows, Dependabot, CodeQL, and CI logs |
| [github-repo-management](skills/github-repo-management/SKILL.md) | Branches, batched commits, test suggestions, and GitHub repository management |
| [repo-hygiene](skills/repo-hygiene/SKILL.md) | Dotfiles, ignore rules, dependency exports, and lockfile sync |
| [project-layout](skills/project-layout/SKILL.md) | Organize frontend, backend, deployment config, tests, scripts, examples, docs, and training code |
| [container-quality](skills/container-quality/SKILL.md) | Shared Docker/Podman builds, Compose overrides, SELinux, and log rotation |
| [backend-quality](skills/backend-quality/SKILL.md) | Backend API contracts, FastAPI OpenAPI, migrations, tests, code standards, and the Nginx public entry point |
| [frontend-quality](skills/frontend-quality/SKILL.md) | HTML/CSS value convergence, render verification, and accessibility |

After installation, you can invoke them explicitly with names such as `$markdown-docs`, or let the
description auto-match.

---

## Installation

### macOS, Linux, and WSL

```bash
git clone https://github.com/autentisitet/repo-maintenance-skills.git ~/repo-maintenance-skills
cd ~/repo-maintenance-skills
./scripts/install.sh
```

By default, `skills/*` is symlinked into `${CODEX_HOME:-~/.codex}/skills`. For an independent copy,
use:

```bash
./scripts/install.sh --copy
```

### Windows PowerShell

```powershell
git clone https://github.com/autentisitet/repo-maintenance-skills.git "$HOME\repo-maintenance-skills"
Set-Location "$HOME\repo-maintenance-skills"
.\scripts\install.ps1
```

Directory junctions are created by default; for an independent copy, use
`.\scripts\install.ps1 -Copy`.

`--force` / `-Force` only replaces links that point at this repository or copies marked by this
project's installation marker. When it encounters a same-named directory of unknown origin, it
stops to avoid deleting a skill the user maintains themselves.

---

## Updating

Symlink or junction installs take effect after pulling the repository:

```bash
git pull
```

Copy installs need to overwrite the corresponding copy again:

```bash
./scripts/install.sh --copy --force
```

On Windows use `.\scripts\install.ps1 -Copy -Force`. Only links created by this project or copies
marked with the installation marker will be replaced.

---

## Structure

```text
repo-maintenance-skills/
├── evals/
│   ├── README.md
│   └── cases.yaml
├── requirements.txt
├── scripts/
│   ├── install.sh
│   ├── install.ps1
│   ├── test_skill_examples.py
│   ├── test_validate_skills.py
│   ├── validate_skill_evals.py
│   └── validate_skills.py
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        ├── scripts/
        └── assets/
```

Directories other than `SKILL.md` are created as needed; empty directories and placeholder files
are not kept.

---

## Validation

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate_skills.py
python3 scripts/test_validate_skills.py
python3 scripts/test_skill_examples.py
python3 scripts/validate_skill_evals.py
python3 skills/markdown-docs/scripts/section-dividers.py --check .
bash -n scripts/install.sh skills/*/scripts/*.sh
```

The validator uses real YAML parsing to check frontmatter, directory naming, internal links, and
`agents/openai.yaml`. The eval validation only confirms that [evals/cases.yaml](evals/cases.yaml)
covers the five case categories completely; it does not call a model and cannot prove that a skill
will trigger or execute correctly. See [evals/README.md](evals/README.md) for behavior verification.

When adding or modifying a skill, you can invoke `$codex-skill-authoring` and then run the checks
above.

---

## Design conventions

- **Personal workflow first.** Personal repeated needs, terminology, and preferences can directly
  become constraints; don't rewrite them for generality.
- **Only write information that changes decisions.** Don't repeat basic capabilities and generic
  tutorials that Codex already has.
- **Split on demand.** `SKILL.md` keeps shared constraints; conditional details go into
  `references/`; deterministic operations go into `scripts/`.
- **Keep wording consistent with constraint strength.** Safety and correctness requirements use
  "must/never"; minimum scope uses "at least"; experiential practices use "recommend/usually";
  conditional tasks use "if/when".
- **Control context cost.** A few skills with real gains are more valuable than many thin skills.

---

## License

This project is licensed under the [MIT License](LICENSE).

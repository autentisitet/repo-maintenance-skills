---
name: markdown-docs
description: Use when writing or revising repository Markdown such as README, CHANGELOG, CONTRIBUTING, issue templates, SECURITY, and DISCLAIMER files. Verify the target renderer and repository markdownlint rules. Do not use for code comments or temporary notes outside a repository.
metadata:
  short-description: Write and review repository Markdown and community documents
---

# Markdown Documentation

Load only the reference for the current document type.

| Document | Reference |
| --- | --- |
| README, badges, contents, math, diagrams, logos | [readme.md](references/readme.md) |
| CHANGELOG | [changelog.md](references/changelog.md) |
| Issue templates, CONTRIBUTING, SECURITY, DISCLAIMER, LICENSE | [community.md](references/community.md) |

## Shared Constraints

1. Confirm the target renderer. GitHub and editor previews can differ in HTML allowlists, Mermaid versions, and anchor generation. Inspect actual rendered output when these features are involved.
2. Follow existing markdownlint configuration and CI checks. If the repository chooses to add markdownlint, adapt [assets/markdownlint.json](assets/markdownlint.json).
3. Change a rule explicitly and explain why when it obstructs useful writing; do not evade it through meaningless formatting.
4. After adding or renaming documentation, update README contents and relative links.
5. In files with multiple level-two headings, place a standalone `---` between adjacent level-two sections with one blank line around it. Do not add one mechanically before the first level-two heading, and do not alter fenced examples.

For bulk formatting, locate the installed skill and run:

```bash
skill_dir="${CODEX_HOME:-$HOME/.codex}/skills/markdown-docs"
python3 "$skill_dir/scripts/section-dividers.py" .
python3 "$skill_dir/scripts/section-dividers.py" --check .
```

---

## Language

- Match the document's chosen language and terminology consistently. In Chinese prose, use full-width punctuation and spacing between Chinese and Latin text where appropriate; keep code, paths, and commands verbatim.
- Prefer direct sentences. Use lists only for genuinely parallel items.

# README

## Content Order

Explain what the project is, what problem it solves, how to use it, how it works, and known limits.

- Use established terminology from domain textbooks, standards, or authoritative documentation, and keep it consistent.
- Let readers determine audience, scope, and first-use steps quickly.
- Do not write the README as a changelog.
- Add a contents section when the document is long enough to need navigation, and verify rendered anchors.

---

## Bilingual Documents

When maintaining `README.md` and `README_zh.md`:

- Link them at the top with `[English](README.md) | [中文](README_zh.md)`.
- Keep section order, code blocks, tables, and badges synchronized.
- Treat an outdated translation as a defect because readers will assume it describes current behavior.

---

## Badges

Add only badges that help readers assess real project state and point to maintained targets, for example:

```markdown
[![version](https://img.shields.io/github/v/release/OWNER/REPO)](https://github.com/OWNER/REPO/releases)
[![ci](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/release.yml?label=release)](https://github.com/OWNER/REPO/actions/workflows/release.yml)
```

Verify that the workflow, release, and default branch exist before adding the badge.

---

## Math and Diagrams

- Use `$...$` for inline math and `$$...$$` for display math. GitHub renders LaTeX natively; VS Code needs an extension such as Markdown+Math. Before committing, inspect the GitHub rendering and confirm no `$` is shown literally, as commonly happens with currency symbols or missing escapes.
- Use Mermaid for architecture and data flow only when the result remains readable. Split dense diagrams and validate against the target renderer rather than a different Mermaid version.

---

## Performance Data

Keep reproducible measurement scripts in the repository and state warmup, repetitions, statistic, hardware, drivers, and input size. Include the formula behind derived values such as throughput.

---

## Logos and Media

Use clear, accessible assets with known licensing. Prefer SVG for simple logos and appropriate bitmap formats for photos or textures. Include useful alternative text.

To center a logo on GitHub:

```html
<p align="center"><img src="assets/logo.svg" width="160" alt="logo"></p>
```

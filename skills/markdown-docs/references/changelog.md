# CHANGELOG

## Version Links

When using reference-style version links, define the release or tag targets at the end of the file:

```markdown
[v1.2.0]: https://github.com/OWNER/REPO/releases/tag/v1.2.0
```

The latest version may sit at the top or the bottom, but use only one ordering convention throughout the document.

If early history has no tag, place the relevant Git history under `Earlier History` instead of inventing versions.

---

## Incorrect Historical Version Labels

When a commit message and actual tag disagree:

1. Confirm whether it was a typo or the assessment at the time.
2. If it was an assessment difference, explain it under `Historical version-label note`.
3. Do not silently rewrite historical entries.

---

## Released and Unreleased Changes

Do not rewrite released entries merely to repackage history. Fix spelling, broken links, and factual errors, but document corrections that change release meaning.

Place unreleased work under `## [Unreleased]`. Do not assign an unknown release date.

---

## Tone

- State what changed and who is affected; avoid marketing language.
- Group breaking changes and provide migration guidance.
- Follow the repository's existing categories. If it uses Keep a Changelog, use Added, Changed, Deprecated, Removed, Fixed, and Security consistently.

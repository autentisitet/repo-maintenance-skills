---
name: frontend-quality
description: Use when writing or reviewing HTML/CSS interfaces, including consolidating design values, verifying real rendering with screenshots, and checking accessibility and browser compatibility. Applies to static pages and small frontends. Do not use for component-library API design or frontend framework selection.
metadata:
  short-description: Review interface values, rendering, accessibility, and compatibility
---

# Frontend Quality

## Available Scripts

- [scripts/audit-css-values.sh](scripts/audit-css-values.sh): print CSS/SCSS value distributions for consolidation review.
- [scripts/screenshot.sh](scripts/screenshot.sh): capture a page with headless Chrome for render verification; set `CHROME_PATH` when the browser cannot be discovered.

Workflow: audit value spread with `audit-css-values.sh`, start a local server and capture representative viewports with `screenshot.sh`, then open the images and inspect the issues described below.

---

## Source

- Minified CSS is a valid artifact, but it must not be the only source. Keep an editable source and a reproducible build path.
- Consolidate radius, spacing, typography, shadows, and colors into a coherent token set. Reuse an existing semantically suitable value before adding another near-duplicate; for example, when `--space-2: 8px` already exists, first decide whether 8px is acceptable and add a token only when it clearly does not satisfy that case.
- Run [scripts/audit-css-values.sh](scripts/audit-css-values.sh) to identify low-frequency values for review. Keep values with a real semantic or component constraint.
- Before adding `!important`, inspect cascade order, scope, and third-party boundaries. A narrowly scoped override of uncontrollable inline or vendor styles can be valid.

---

## Render Verification

Do not infer layout correctness from source alone. Start the page and capture representative views:

```bash
python3 -m http.server 8000 --directory ./dist &
"<skill-dir>/scripts/screenshot.sh" http://localhost:8000 1440x900 out/desktop.png
"<skill-dir>/scripts/screenshot.sh" http://localhost:8000 390x844 out/mobile.png
```

- Check at least one wide and one narrow viewport; cover both sides of meaningful breakpoints.
- Open the screenshots and inspect overflow, overlap, clipping, unreadable type, and insufficient contrast.
- Inspect hover, focus, and disabled states separately because static screenshots do not cover them.
- Test dark mode independently instead of assuming automatic inversion is usable.

---

## Accessibility

- Meet WCAG AA contrast: 4.5:1 for normal text and 3:1 for large text.
- Keep every interactive element keyboard reachable and provide visible `:focus-visible` styling.
- Give informative images meaningful `alt`; use `alt=""` for decorative images.
- Do not communicate state through color alone.
- Associate form controls with labels instead of relying only on placeholders.

---

## Compatibility

- Check target-browser support before using a feature.
- Use `@supports` fallbacks when older browsers must remain supported; do not silently degrade into a broken layout.
- Avoid relying on behavior implemented by only one browser engine.

# CI Logs

## Redaction

GitHub masks registered secret values, but encoded, truncated, or concatenated derivatives may no longer match. Avoid printing secrets at all:

```bash
token="${{ secrets.TOKEN }}"
curl -H "Authorization: Bearer ${{ secrets.TOKEN }}" https://example.com
```

When a derived value may enter logs, mask it before its first output:

```bash
derived="$(printf '%s' "${{ secrets.TOKEN }}" | base64)"
echo "::add-mask::$derived"
```

Masking is not retroactive.

---

## Bound Output

Prefer summaries and print complete logs only on failure:

```bash
if ! command >command.log 2>&1; then
  tail -200 command.log
  exit 1
fi
```

Use `tail`, not `cat`, for potentially large logs.

---

## Annotations and Groups

```bash
echo "::error file=src/main.py,line=42::unexpected token"
echo "::warning::cache miss, rebuilding"
echo "::notice::using fallback mirror"
```

`file=` and `line=` make errors clickable in the pull-request diff. Keep annotation messages single-line, since newlines truncate them.

```bash
echo "::group::dependency details"
command
echo "::endgroup::"
```

Keep annotations free of secrets. Group verbose successful output so the failure signal remains visible.

---

## Job Summary

Write durable test statistics or performance comparisons to `$GITHUB_STEP_SUMMARY` instead of burying them in logs:

```bash
{
  echo "## Test summary"
  echo "| suite | passed | failed |"
  echo "| --- | --- | --- |"
  echo "| unit | ${PASSED} | ${FAILED} |"
} >> "$GITHUB_STEP_SUMMARY"
```

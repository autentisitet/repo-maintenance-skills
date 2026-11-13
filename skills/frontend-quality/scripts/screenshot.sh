#!/usr/bin/env bash
# Capture a page with headless Chrome for render verification.
#
# Usage: ./screenshot.sh <url> [WxH] [out.png]
#   ./screenshot.sh http://localhost:8000 1440x900 out/desktop.png
#
# Set CHROME_PATH when Chrome/Chromium cannot be discovered.
set -euo pipefail

usage() {
  echo "Usage: $0 <url> [WxH] [out.png]" >&2
  exit 2
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  printf '%s\n' \
    "Usage: $0 <url> [WxH] [out.png]" \
    "Set CHROME_PATH for Chrome/Chromium; default size is 1440x900."
  exit 0
fi

[[ $# -ge 1 ]] || usage
url="$1"
size="${2:-1440x900}"
out="${3:-screenshot.png}"

box="${size/x/,}"

chrome="${CHROME_PATH:-}"
if [[ -z "$chrome" ]]; then
  for candidate in google-chrome google-chrome-stable chromium chromium-browser chrome msedge; do
    if command -v "$candidate" >/dev/null 2>&1; then
      chrome="$(command -v "$candidate")"
      break
    fi
  done
fi
if [[ -z "$chrome" ]]; then
  for candidate in \
    "/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
    if [[ -x "$candidate" ]]; then
      chrome="$candidate"
      break
    fi
  done
fi
if [[ -z "$chrome" ]]; then
  echo "Chrome/Chromium not found. Set CHROME_PATH to an executable." >&2
  exit 1
fi

if command -v "$chrome" >/dev/null 2>&1; then
  chrome="$(command -v "$chrome")"
elif [[ ! -x "$chrome" ]]; then
  echo "CHROME_PATH is not executable: $chrome" >&2
  exit 1
fi

mkdir -p "$(dirname "$out")"

err_log="$(mktemp)"
profile_dir="$(mktemp -d)"
cleanup() {
  rm -rf -- "$profile_dir"
  rm -f -- "$err_log"
}
trap cleanup EXIT

if ! "$chrome" \
  --headless=new \
  --disable-gpu \
  --hide-scrollbars \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir="$profile_dir" \
  --virtual-time-budget=3000 \
  --window-size="$box" \
  --screenshot="$out" \
  "$url" >/dev/null 2>"$err_log"; then
  echo "Browser execution failed ($chrome):" >&2
  tail -20 "$err_log" >&2
  exit 1
fi

if [[ ! -s "$out" ]]; then
  echo "Screenshot failed; no output was created at $out" >&2
  exit 1
fi

echo "Saved: $out ($box)"

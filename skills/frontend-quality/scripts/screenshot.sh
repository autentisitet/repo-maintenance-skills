#!/usr/bin/env bash
# 用 headless Chrome 截取页面，用于确认实际渲染效果。
#
# 用法: ./screenshot.sh <url> [WxH] [out.png]
#   ./screenshot.sh http://localhost:8000 1440x900 out/desktop.png
#
# 找不到浏览器时，用 CHROME_PATH 指定可执行文件。
set -euo pipefail

usage() {
  echo "用法: $0 <url> [WxH] [out.png]" >&2
  exit 2
}

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
  echo "找不到 Chrome/Chromium。设置 CHROME_PATH 指向可执行文件。" >&2
  exit 1
fi

if command -v "$chrome" >/dev/null 2>&1; then
  chrome="$(command -v "$chrome")"
elif [[ ! -x "$chrome" ]]; then
  echo "CHROME_PATH 不可执行: $chrome" >&2
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
  echo "浏览器执行失败（$chrome）：" >&2
  tail -20 "$err_log" >&2
  exit 1
fi

if [[ ! -s "$out" ]]; then
  echo "截图失败，未生成 $out" >&2
  exit 1
fi

echo "已保存: $out ($box)"

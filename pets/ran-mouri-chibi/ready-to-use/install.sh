#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}/pets/ran-chibi-clear-v2"

if [[ ! -s "$ROOT/pet.json" || ! -s "$ROOT/spritesheet.webp" ]]; then
  echo "安装包不完整：缺少 pet.json 或 spritesheet.webp" >&2
  exit 1
fi
mkdir -p "$DEST"
install -m 0644 "$ROOT/pet.json" "$DEST/pet.json"
install -m 0644 "$ROOT/spritesheet.webp" "$DEST/spritesheet.webp"

echo "已独立安装 小兰 · 清晰Q版：$DEST"
echo "现有 ran-watercolor 未被修改。请完全退出并重新启动 Codex。"

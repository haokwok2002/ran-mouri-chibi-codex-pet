#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}/pets/porco-rosso-chibi-v1"
[[ -s "$ROOT/pet.json" && -s "$ROOT/spritesheet.webp" ]] || { echo "安装包不完整：缺少 pet.json 或 spritesheet.webp" >&2; exit 1; }
mkdir -p "$DEST"
install -m 0644 "$ROOT/pet.json" "$DEST/pet.json"
install -m 0644 "$ROOT/spritesheet.webp" "$DEST/spritesheet.webp"
echo "已安装 红猪 · 飞行员Q版：$DEST"
echo "请完全退出并重新启动 Codex Desktop。"

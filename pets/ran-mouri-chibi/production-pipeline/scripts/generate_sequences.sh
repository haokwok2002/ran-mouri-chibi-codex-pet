#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKSPACE_ROOT="$(cd "$ROOT/../../.." && pwd)"
GEN="${CODEX_PET_IMAGE_GENERATOR:-$WORKSPACE_ROOT/tools/image-api/generate_image.py}"
IDENTITY="$ROOT/references/xiaolan-reference.png"
ANCHOR="$ROOT/source/anchor-green.png"
OUT="$ROOT/source/sequences/source"
mkdir -p "$OUT"

generate() {
  local name="$1" size="$2"
  local output="$OUT/$name-green.png"
  if [[ -s "$output" ]]; then
    echo "[跳过] $name 已存在"
    return
  fi
  local prompt
  prompt="$(<"$ROOT/prompts/sequence-common.txt")"$'\n'"$(<"$ROOT/prompts/$name.txt")"
  "${PYTHON:-python3}" "$GEN" \
    --ref "$IDENTITY" \
    --ref "$ANCHOR" \
    --prompt "$prompt" \
    --size "$size" \
    --quality high \
    --output "$output"
}

run_batch() {
  local pids=()
  while [[ "$#" -gt 0 ]]; do
    generate "$1" "$2" &
    pids+=("$!")
    shift 2
  done
  local status=0 pid
  for pid in "${pids[@]}"; do
    wait "$pid" || status=1
  done
  return "$status"
}

run_batch idle 2048x1024 run-right 2048x1024 waving 1024x1024
run_batch jumping 1536x1024 failed 2048x1024 waiting 1536x1024
run_batch working 1536x1024 review 1536x1024 look 2048x2048

echo "[完成] 第二版 Q 版逐帧分镜已生成"

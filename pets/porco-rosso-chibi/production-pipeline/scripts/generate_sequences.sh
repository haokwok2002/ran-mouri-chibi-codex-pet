#!/usr/bin/env bash
set -euo pipefail

PIPELINE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PET_ROOT="$(cd "$PIPELINE_ROOT/.." && pwd)"
WORKSPACE_ROOT="$(cd "$PET_ROOT/../.." && pwd)"
GENERATOR="${CODEX_PET_IMAGE_GENERATOR:-$WORKSPACE_ROOT/tools/image-api/generate_image.py}"
REFERENCE="$PIPELINE_ROOT/references/porco-rosso-reference-green.png"
COMMON="$PIPELINE_ROOT/prompts/sequence-common.txt"
OUT="$PIPELINE_ROOT/source/sequences/source"

[[ -f "$GENERATOR" ]] || { echo "找不到共享图片生成器：$GENERATOR" >&2; exit 1; }
[[ -s "$REFERENCE" ]] || { echo "找不到身份参考图：$REFERENCE" >&2; exit 1; }
mkdir -p "$OUT"

generate() {
  local name="$1" size="$2" prompt_name="$3"
  local output="$OUT/$name-green.png"
  [[ ! -s "$output" ]] || { echo "[跳过] $name 已存在"; return; }
  "${PYTHON:-python3}" "$GENERATOR" \
    --ref "$REFERENCE" \
    --prompt "$(<"$COMMON")"$'\n'"$(<"$PIPELINE_ROOT/prompts/$prompt_name")" \
    --size "$size" \
    --quality high \
    --output "$output"
}

generate idle 2048x1024 idle.txt
generate running-right 2048x1024 running-right.txt
generate waving 1024x1024 waving.txt
generate jumping 1536x1024 jumping.txt
generate failed 2048x1024 failed.txt
generate waiting 1536x1024 waiting.txt
generate running 1536x1024 working.txt
generate review 1536x1024 review.txt

echo "[完成] 红猪 V1 标准动作分镜已生成"

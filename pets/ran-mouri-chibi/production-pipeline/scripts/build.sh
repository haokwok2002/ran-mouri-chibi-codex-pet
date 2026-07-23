#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MATTING="${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py"
SOURCE="$ROOT/source/sequences/source"
MATTED="$ROOT/source/sequences/matted"
mkdir -p "$MATTED"

if [[ ! -f "$MATTING" ]]; then
  echo "找不到抠像工具：$MATTING" >&2
  exit 1
fi

for name in idle run-right waving jumping failed waiting working review look; do
  input="$SOURCE/$name-green.png"
  output="$MATTED/$name.png"
  if [[ ! -s "$input" ]]; then
    echo "缺少生成素材：$input" >&2
    echo "请先运行 bash production-pipeline/scripts/generate_sequences.sh" >&2
    exit 1
  fi
  "${PYTHON:-python3}" "$MATTING" \
    --input "$input" \
    --out "$output" \
    --auto-key border \
    --soft-matte \
    --transparent-threshold 12 \
    --opaque-threshold 220 \
    --despill \
    --force
done

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/ran-chibi-clear-v2-pycache" \
  "${PYTHON:-python3}" "$ROOT/scripts/build_pet.py"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/ran-chibi-clear-v2-pycache" \
  "${PYTHON:-python3}" "$ROOT/scripts/validate_pet.py"
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/ran-chibi-clear-v2-pycache" \
  "${PYTHON:-python3}" "$ROOT/scripts/audit_quality.py"

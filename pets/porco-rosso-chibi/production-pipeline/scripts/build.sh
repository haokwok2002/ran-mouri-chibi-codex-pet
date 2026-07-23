#!/usr/bin/env bash
set -euo pipefail

PIPELINE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MATTING="${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py"
[[ -f "$MATTING" ]] || { echo "找不到抠像工具：$MATTING" >&2; exit 1; }

for name in idle running-right waving jumping failed waiting running review; do
  input="$PIPELINE_ROOT/source/sequences/source/$name-green.png"
  output="$PIPELINE_ROOT/source/sequences/matted/$name-green.png"
  [[ -s "$input" ]] || { echo "缺少分镜：$input" >&2; exit 1; }
  "${PYTHON:-python3}" "$MATTING" --input "$input" --out "$output" --auto-key border --soft-matte --transparent-threshold 12 --opaque-threshold 220 --despill --force
done

"${PYTHON:-python3}" "$PIPELINE_ROOT/scripts/build_pet_v1.py"
"${PYTHON:-python3}" "$PIPELINE_ROOT/scripts/validate_pet_v1.py"
"${PYTHON:-python3}" "$PIPELINE_ROOT/scripts/audit_quality_v1.py"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PET_ID="${1:-}"

case "$PET_ID" in
  ran-mouri-chibi|porco-rosso-chibi|mitsuha-miyamizu-chibi) ;;
  *)
    printf '用法: bash install.sh <ran-mouri-chibi|porco-rosso-chibi|mitsuha-miyamizu-chibi>\n' >&2
    exit 2
    ;;
esac

exec bash "$ROOT/pets/$PET_ID/ready-to-use/install.sh"

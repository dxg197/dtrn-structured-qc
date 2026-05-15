#!/usr/bin/env bash
set -euo pipefail

CACHE_DIR="${CACHE_DIR:-v23_cache}"
ROTATION="${ROTATION:-}"

ARGS=(--output-dir "$CACHE_DIR" --bond 1.6788 --basis cc-pvdz --ncas 12 --nelecas 12)
if [ -n "$ROTATION" ]; then
  if [ ! -f "$ROTATION" ]; then
    echo "Missing ROTATION: $ROTATION"
    exit 1
  fi
  ARGS+=(--active-rotation "$ROTATION")
fi

python3 -m cr2v23.cli build-integrals "${ARGS[@]}"

echo
echo "Cache contents:"
ls -lah "$CACHE_DIR"
if [ -f "$CACHE_DIR/active_integrals_cr2_cas12.meta.json" ]; then
  cat "$CACHE_DIR/active_integrals_cr2_cas12.meta.json"
fi

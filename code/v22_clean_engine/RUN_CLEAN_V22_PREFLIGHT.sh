#!/usr/bin/env bash
set -euo pipefail
CACHE_DIR="${CACHE_DIR:-v22_clean_cache}"
ROTATION="${ROTATION:-cr2_v1435_no_results/01_make_no/active_rotation_from_restart.npy}"
ARGS=(--output-dir "$CACHE_DIR" --bond 1.6788 --basis cc-pvdz --ncas 12 --nelecas 12)
if [ -f "$ROTATION" ]; then
  echo "Using active rotation: $ROTATION"
  ARGS+=(--active-rotation "$ROTATION")
else
  echo "No active rotation at $ROTATION; building canonical CASSCF active-space integrals."
fi
python3 -m cr2v22.cli build-integrals "${ARGS[@]}"
echo
ls -lah "$CACHE_DIR"

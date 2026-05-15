#!/usr/bin/env bash
set -euo pipefail
CACHE_DIR="${CACHE_DIR:-v22_clean_cache}"
INTEGRALS="${INTEGRALS:-$CACHE_DIR/active_integrals_cr2_cas12.npz}"
OUTPUT_DIR="${OUTPUT_DIR:-v22_clean_runs/from_legacy20k_to0p5_$(date +%Y%m%d_%H%M%S)}"
LEGACY_DIR="${LEGACY_DIR:-}"
if [ -z "$LEGACY_DIR" ]; then
  echo "Set LEGACY_DIR to the v21.3 20k checkpoint directory."
  echo 'Example: LEGACY_DIR="$PWD/v21_3_final_results/step028_restart_r10_to20000" RUN=1 ./RUN_CLEAN_V22_FROM_LEGACY_20K_TO_0P5.sh'
  exit 1
fi
if [ ! -d "$LEGACY_DIR" ]; then
  echo "Missing LEGACY_DIR: $LEGACY_DIR"
  exit 1
fi
if [ ! -f "$INTEGRALS" ]; then
  echo "Missing integrals at $INTEGRALS; running preflight build first."
  ./RUN_CLEAN_V22_PREFLIGHT.sh
fi
CMD=(python3 -m cr2v22.cli run-selected-ci
  --integrals "$INTEGRALS"
  --output-dir "$OUTPUT_DIR"
  --restart-dir "$LEGACY_DIR"
  --legacy-layout "${LEGACY_LAYOUT:-auto}"
  --target-gap-mha "${TARGET_GAP_MHA:-0.5}"
  --max-dim "${MAX_DIM:-30000}"
  --walltime-seconds "${WALLTIME_SECONDS:-86400}"
  --add-per-iter "${ADD_PER_ITER:-500}"
  --candidate-limit "${CANDIDATE_LIMIT:-300000}"
  --rank-filter "${RANK_FILTER:-12}"
  --unlock-rank "${UNLOCK_RANK:-12}"
  --eig-tol "${EIG_TOL:-1e-8}"
  --eig-maxiter "${EIG_MAXITER:-300}"
)
printf '%q ' "${CMD[@]}"; echo
if [ "${RUN:-0}" = "1" ]; then
  "${CMD[@]}"
else
  echo "Dry-run only. To execute: RUN=1."
fi

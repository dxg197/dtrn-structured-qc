#!/usr/bin/env bash
set -euo pipefail

CACHE_DIR="${CACHE_DIR:-v23_cache}"
INTEGRALS="${INTEGRALS:-$CACHE_DIR/active_integrals_cr2_cas12.npz}"
RESTART_DIR="${RESTART_DIR:-}"
OUTPUT_DIR="${OUTPUT_DIR:-v23_runs/continue_clean_en2_$(date +%Y%m%d_%H%M%S)}"

if [ -z "$RESTART_DIR" ]; then
  echo "Set RESTART_DIR to a clean v22/v23 checkpoint directory."
  echo 'Example: RESTART_DIR="$PWD/v22_clean_runs/from_zero_24h_20260514_170418" RUN=1 ./RUN_V23_CONTINUE_CLEAN_CHECKPOINT_TO_0P5.sh'
  exit 1
fi
if [ ! -d "$RESTART_DIR" ]; then
  echo "Missing RESTART_DIR: $RESTART_DIR"
  exit 1
fi
if [ ! -f "$RESTART_DIR/selected_pairs_final.npy" ] || [ ! -f "$RESTART_DIR/selected_coeff_final.npy" ]; then
  echo "RESTART_DIR must contain selected_pairs_final.npy and selected_coeff_final.npy"
  exit 1
fi
if [ ! -f "$INTEGRALS" ]; then
  echo "Missing integrals at $INTEGRALS; running preflight first."
  ./RUN_V23_PREFLIGHT.sh
fi

CMD=(python3 -m cr2v23.cli run-selected-ci
  --integrals "$INTEGRALS"
  --output-dir "$OUTPUT_DIR"
  --restart-dir "$RESTART_DIR"
  --target-gap-mha "${TARGET_GAP_MHA:-0.5}"
  --max-dim "${MAX_DIM:-120000}"
  --walltime-seconds "${WALLTIME_SECONDS:-86400}"
  --add-per-iter "${ADD_PER_ITER:-1000}"
  --candidate-limit "${CANDIDATE_LIMIT:-853776}"
  --rank-filter "${RANK_FILTER:-12}"
  --unlock-rank "${UNLOCK_RANK:-12}"
  --score-mode "${SCORE_MODE:-en2}"
  --denom-floor "${DENOM_FLOOR:-1e-8}"
  --hybrid-residual-weight "${HYBRID_RESIDUAL_WEIGHT:-0.05}"
  --eig-tol "${EIG_TOL:-1e-8}"
  --eig-maxiter "${EIG_MAXITER:-300}"
)

printf '%q ' "${CMD[@]}"
echo

if [ "${RUN:-0}" = "1" ]; then
  "${CMD[@]}"
else
  echo "Dry-run only. To execute: RUN=1."
fi

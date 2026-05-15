#!/usr/bin/env bash
set -euo pipefail
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
ENGINE="$ROOT/code/v23_clean_en2_engine"
OUT="$ROOT/reproduced_runs/v23_from_zero_$(date +%Y%m%d_%H%M%S)"
cd "$ENGINE"
if [ ! -f "v23_cache/active_integrals_cr2_cas12.npz" ]; then
  ./RUN_V23_PREFLIGHT.sh
fi
CMD=(python3 -m cr2v23.cli run-selected-ci
  --integrals "v23_cache/active_integrals_cr2_cas12.npz"
  --output-dir "$OUT"
  --target-gap-mha 0.5
  --max-dim 120000
  --walltime-seconds 86400
  --add-per-iter 1000
  --candidate-limit 853776
  --rank-filter 12
  --unlock-rank 12
  --score-mode en2
  --denom-floor 1e-8
  --hybrid-residual-weight 0.05
  --eig-tol 1e-8
  --eig-maxiter 300
)
printf '%q ' "${CMD[@]}"; echo
if [ "${RUN:-0}" = "1" ]; then
  "${CMD[@]}"
else
  echo "Dry run only. Use RUN=1 scripts/reproduce_v23_from_zero.sh"
fi

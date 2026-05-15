# Cr2 v23 Clean EN2 Engine

v23 keeps the clean v22 architecture but replaces raw-residual selection with an EN2/PT2-style scoring rule.

Clean v22 selection used roughly:

```text
score_i = |H_iS c_S|
```

v23 defaults to:

```text
score_i = |H_iS c_S|^2 / max(|E_var - H_ii|, denom_floor)
```

The variational solve is still a normal selected-CI solve, so the reported `E_var` remains variational. EN2 is only a determinant-selection heuristic and diagnostic.

## What is different from legacy v21.x

v23 does **not** call the old v14.33/v21.x selected-CI engine and does **not** use a Jordan-Wigner Pauli cache. It uses:

```text
PySCF CASSCF active-space integrals
PySCF direct_spin1 contractions
fixed CAS(12,12) alpha/beta determinant sector
matrix-free selected-subspace eigsh
EN2-scored full-sector residual candidate selection
```

This avoids the old `29709` vs `29717` Pauli-cache failure mode.

## Is this a legitimate solver?

Yes, if the active-space integrals are correct. v23 is a variational selected-CI solver in the fixed CAS sector. Candidate selection can be heuristic, but the final energy is obtained by diagonalizing the Hamiltonian in the selected determinant subspace, so it is variational with respect to the chosen active-space Hamiltonian.

It still needs validation before replacing paper-safe legacy numbers:

1. Check the PySCF CASSCF/CASCI reference in the cache metadata.
2. Confirm monotone `E_var`.
3. Compare small/medium checkpoints against a known full-sector or trusted selected-CI result.
4. Treat EN2/PT2 values as diagnostic only.

## Install

```bash
unzip Cr2_v23_clean_en2_engine.zip
cd Cr2_v23_clean_en2_engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you already have a working PySCF environment, use that environment instead.

## Build integrals

```bash
./RUN_V23_PREFLIGHT.sh
```

To use an active rotation:

```bash
ROTATION="/path/to/active_rotation_from_restart.npy" ./RUN_V23_PREFLIGHT.sh
```

## From-zero 24h attempt

```bash
RUN=1 ./RUN_V23_FROM_ZERO_24H_EN2.sh
```

## Continue a clean v22/v23 checkpoint

This expects clean-engine files:

```text
selected_pairs_final.npy
selected_coeff_final.npy
cr2_v23_clean_final.json or cr2_v22_clean_final.json
```

Run:

```bash
RESTART_DIR="/path/to/clean/checkpoint" RUN=1 ./RUN_V23_CONTINUE_CLEAN_CHECKPOINT_TO_0P5.sh
```

## Main defaults

```text
score_mode=en2
add_per_iter=1000
candidate_limit=853776
max_dim=120000
target_gap_mha=0.5
walltime_seconds=86400
rank_filter=12
```

For a smaller smoke test:

```bash
RUN=1 MAX_DIM=5000 ADD_PER_ITER=500 WALLTIME_SECONDS=3600 ./RUN_V23_FROM_ZERO_24H_EN2.sh
```


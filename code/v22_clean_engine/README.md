# Cr2 v22 Clean Engine: standalone selected-CI for CAS(12,12)

This package is a clean v22 engine that **does not call the old v14.33/v14.35/v21.x selected-CI engine**.

It is designed to avoid the failure mode where the legacy engine loads the wrong cached Hamiltonian:

```text
29709 Pauli terms
```

instead of the v21.3/v14.35 natural-orbital lineage. The clean engine uses PySCF active-space integrals and PySCF's optimized `direct_spin1` contraction in the full fixed `(N_alpha, N_beta)` CAS sector. It selects a compact determinant subspace by full-sector residual/coupling scores.

## Why this is different

Legacy path:

```text
PySCF -> JW Pauli cache -> legacy selected-CI engine -> hidden cache/orbital logic
```

Clean v22 path:

```text
PySCF CASSCF active integrals -> full-sector alpha/beta determinant indexing -> residual-selected CI
```

There is no Pauli-term count, no JW cache, and no legacy Hamiltonian cache. The engine validates against the CASSCF/CASCI active-space reference reported by PySCF.

## Install

```bash
unzip Cr2_v22_clean_engine_standalone.zip
cd Cr2_v22_clean_engine_standalone
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

PySCF may take time to install on macOS. If you already have a working PySCF environment, use that instead.

## Preflight

```bash
./RUN_CLEAN_V22_PREFLIGHT.sh
```

## From zero, 24-hour attempt

```bash
RUN=1 ./RUN_CLEAN_V22_FROM_ZERO_24H.sh
```

## Continue from legacy v21.3 20k checkpoint

```bash
LEGACY_DIR="/path/to/step028_restart_r10_to20000" RUN=1 \
./RUN_CLEAN_V22_FROM_LEGACY_20K_TO_0P5.sh
```

The legacy importer supports both common spin-orbital layouts and can auto-detect the one that gives the correct `(N_alpha,N_beta)` for every determinant.

## Important

This is a new engine. It should reproduce or improve the v21.3 20k result before it replaces any paper-safe numbers.


# DTRN PRX Intelligence reproducibility repository

This repository is a GitHub-ready reproducibility package for the manuscript:

**Dissipative Tensor Rotation Networks: A Classical Architecture for Parameter-Efficient Machine Learning and Strongly-Correlated Quantum Chemistry**  
David Garrison, May 2026

It contains the latest PRX draft, primary Cr2 CAS(12,12) result data, supporting clean-v22/v23 code, legacy Cr2 provenance archives, generated analysis tables/plots, and scripts for endpoint verification and rerunning the primary calculation.

## Primary result

The primary quantum-chemistry result is the clean v23 EN2-selected CI Cr2 CAS(12,12)/cc-pVDZ run:

| Quantity | Value |
|---|---:|
| Selected determinants | 102,001 |
| E_var | -2086.650339037541 Ha |
| E_ref / PySCF CASSCF | -2086.650833315363 Ha |
| Gap | 0.4942778218719468 mHa |
| Wall time | 1168.4298000335693 s = 19.47 min |
| Machine | Apple M1 laptop-class, 16 GB RAM |
| Solver | clean active-space selected CI with EN2-style candidate scoring |

EN2 is used only for determinant selection/diagnostics; the reported energy is variational from selected-subspace diagonalization.

## Repository map

```text
paper/                                  latest and historical manuscript drafts
data/primary_v23_en2_from_zero/         extracted primary v23 run files
data/supporting_v22_from_zero/          extracted complete v22 run files
code/v23_clean_en2_engine/              executable clean v23 source
code/v22_clean_engine/                  executable clean v22 source
analysis/                               review plots/CSVs/markdown
tables/run_summary.csv                  endpoint summary
artifacts/                              original raw result/code archives
scripts/verify_primary_results.py       quick endpoint verification
scripts/reproduce_v23_from_zero.sh      rerun v23 primary calculation
```

## Quick verification

```bash
python3 scripts/verify_primary_results.py
```

## Reproduce the primary v23 run

```bash
cd code/v23_clean_en2_engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../..
RUN=1 scripts/reproduce_v23_from_zero.sh
```

The original run reached 0.494 mHa at 102,001 determinants in about 19.5 minutes on an Apple M1 laptop-class machine. Runtime may vary by hardware and PySCF/BLAS configuration.

## Data provenance

Primary extracted files:

- `data/primary_v23_en2_from_zero/cr2_v23_clean_final.json`
- `data/primary_v23_en2_from_zero/progress.csv`
- `data/primary_v23_en2_from_zero/selected_pairs_final.npy`
- `data/primary_v23_en2_from_zero/selected_coeff_final.npy`
- `data/primary_v23_en2_from_zero/top_determinants_final.csv`

All files have SHA256 checksums in `checksums_sha256.txt`; a detailed manifest is in `MANIFEST.csv` and `MANIFEST.json`.

## Important caveat

The clean v22/v23 results are standalone clean-solver results using PySCF active-space integrals and direct `spin1` contractions. They are not direct continuations of the fragile legacy v21.3 Pauli/Jordan-Wigner checkpoint lineage.

## Third-party literature

Third-party PDF papers are not redistributed here. See `docs/EXCLUDED_THIRD_PARTY_PAPERS.md` and the manuscript bibliography.

# Dissipative Tensor Rotation Networks: structured classical tensor factorizations for ML and quantum chemistry

This repository is the planned artifact bundle for the paper:

**Dissipative Tensor Rotation Networks: A Classical Architecture for Parameter-Efficient Machine Learning and Strongly-Correlated Quantum Chemistry**  
David Garrison, May 2026 draft.

This snapshot is based on **DTRN_PRX_v38**. The repository is organized around paper claims and reproducibility, not around the historical development order. The Cr2 CAS(12,12) row is intentionally easy to update once the final v21.4b continuation data are available.

## Current status

- Paper draft: `paper/DTRN_PRX_v38.pdf`
- Current paper-safe result manifest: `results/paper_safe_json/qc_results_current.json`
- Current claim table: `results/summary_tables/paper_claim_status.csv`
- Cr2 CAS(12,12): current v38 row is **1.491 mHa at 16,026 determinants**, with v21.4b restart in progress.
- PT2/EN2 values are diagnostic only. Use `E_var` as the paper-safe quantum-chemistry metric.

## Main claims tracked here

1. DTRN gives logarithmic parameter scaling through Kronecker products of SO(d) factors.
2. Geometry/domain alignment is the decisive inductive bias.
3. PE-GADTRN and DTRN-LoRA provide controlled parameter-efficiency demonstrations.
4. DTRN-inspired selected-CI workflows recover strong Cr2/Fe2 active-space results on commodity hardware.
5. Cr2 CAS(12,12) is currently below 2 mHa and pending final sub-mHa update.

## Repository layout

```text
paper/                  Manuscript PDF, figure/table notes
src/                    Lightweight package namespace and utilities
scripts/                Verification and update scripts
results/                CSV/JSON paper-safe summaries
experiments/            Per-domain README files and run manifests
docs/                   Method, Cr2 timeline, failure modes, reviewer guide
environment/            Python/Mac M1 setup notes
checkpoints_manifest/   Hash/checkpoint manifests and external-artifact instructions
```

## Quick validation

```bash
python3 scripts/verify_qc_results.py
python3 scripts/render_current_tables.py
```

## Updating Cr2 CAS(12,12)

When the final Cr2 CAS(12,12) run completes, prepare a JSON file with the updated result and run:

```bash
python3 scripts/update_cr2_cas12.py --input new_cr2_cas12_result.json
python3 scripts/verify_qc_results.py
```

See `docs/cr2_update_protocol.md` for the expected schema.

## Large artifacts

Large checkpoint files, Hamiltonian caches, and full trained model checkpoints should not be committed directly to Git history. Use GitHub Releases, Git LFS, Zenodo, OSF, or another archival backend. Record every artifact in `checkpoints_manifest/external_artifacts.md` with SHA256 hashes.

# Reviewer reproducibility guide

This repository is designed around verifiable paper claims.

Recommended reviewer entry points:

1. Read `results/summary_tables/paper_claim_status.csv`.
2. Verify quantum-chemistry arithmetic:

```bash
python3 scripts/verify_qc_results.py
```

3. Inspect quantum-chemistry provenance:

```text
results/paper_safe_json/qc_results_current.json
checkpoints_manifest/external_artifacts.md
```

4. Inspect the Cr2 update protocol:

```text
docs/cr2_update_protocol.md
```

Large determinant vectors, full Hamiltonian caches, neural checkpoints, and long raw logs should be published through Releases, Zenodo, OSF, or another archival system with SHA256 hashes.

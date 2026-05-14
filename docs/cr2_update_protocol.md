# Cr2 CAS(12,12) update protocol

The current v38 snapshot is:

```text
selected_dim = 16026
E_var = -2086.649342 Ha
gap = 1.491 mHa
active_rotation_tag = active_rotation:c65788197e7dc63e
```

When the final Cr2 CAS(12,12) run arrives, update the repository with a JSON file like:

```json
{
  "method": "v21.4b natural-orbital adaptive-rank selected-CI",
  "selected_dim_or_basis": 18000,
  "E_var_Ha": -2086.650000000000,
  "E_ref_Ha": -2086.650833304065,
  "gap_mHa": 0.833304,
  "correlation_recovery_pct": 99.88,
  "N": 12.0,
  "Sz": 0.0,
  "status": "sub-mHa validated",
  "active_rotation_tag": "active_rotation:c65788197e7dc63e",
  "notes": "Final paper-safe CAS(12,12) result. PT2 diagnostic only."
}
```

Then run:

```bash
python3 scripts/update_cr2_cas12.py --input new_cr2_cas12_result.json
python3 scripts/verify_qc_results.py
python3 scripts/render_current_tables.py
```

Checklist before accepting a Cr2 CAS(12,12) result:

- `E_var` is variational and monotone relative to the previous accepted selected space.
- `N ~= 12`.
- `Sz = 0`.
- The active rotation tag is `active_rotation:c65788197e7dc63e`.
- Hamiltonian/orbital basis matches the v14.35/v21.1/v21.3 natural-orbital checkpoint lineage.
- PT2/EN2 is diagnostic only.

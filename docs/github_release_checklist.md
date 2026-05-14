# GitHub release checklist

Before public release:

- [ ] Replace `LICENSE_PENDING.md` with final license.
- [ ] Update `CITATION.cff` with arXiv DOI/identifier.
- [ ] Replace `paper/DTRN_PRX_v38.pdf` with final PDF if newer.
- [ ] Update Cr2 CAS(12,12) row if final data are available.
- [ ] Run `python3 scripts/verify_qc_results.py`.
- [ ] Run `python3 scripts/render_current_tables.py`.
- [ ] Add SHA256 hashes for large external artifacts.
- [ ] Confirm README does not claim unavailable reproduction scripts.
- [ ] Confirm no stale Fe2 or Cr2 text remains in docs.

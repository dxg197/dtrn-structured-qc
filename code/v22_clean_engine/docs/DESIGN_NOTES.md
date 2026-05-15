# v22 clean engine design notes

## Reason for rebuilding

The legacy v14.33/v14.35/v21.x engine stack repeatedly loaded a `29709`-term Hamiltonian when the intended v21.3 natural-orbital lineage required the `29717`-term path. That made the first actual diagonalization jump from the correct ~1.10 mHa region to hundreds of mHa. Wrapping the old engine is therefore not enough.

## New representation

The clean engine uses PySCF active-space integrals and works directly in the fixed `(N_alpha,N_beta)` CAS sector.

For Cr2 CAS(12,12):

```text
N_alpha = 6
N_beta  = 6
number of alpha strings = C(12,6) = 924
number of beta strings  = C(12,6) = 924
full sector size        = 853,776 determinants
```

A selected determinant is stored as one integer:

```text
flat = alpha_address * n_beta + beta_address
```

## Selection method

At each iteration:

1. Scatter selected coefficients into the full CAS vector.
2. Apply PySCF `direct_spin1.contract_2e`.
3. Use the external full-sector residual/coupling magnitude to rank candidates.
4. Add the top candidates.
5. Solve the selected subspace as a linear operator using `eigsh`.

This avoids explicit Pauli caches.

## Advantages

- No JW Pauli term count mismatch.
- No hidden legacy cache key.
- Full-sector external scoring is exhaustive within the CAS sector.
- Determinants can be imported from legacy bitstrings with layout detection.
- Every checkpoint is self-describing and restartable within the clean engine.

## Limitations

- The engine relies on PySCF `direct_spin1` contractions and may need profiling.
- It is not yet optimized with incremental matrix updates.
- Legacy restart determinant spin-orbital layout must be validated.
- The clean engine must reproduce v21.3 20k before replacing paper-safe numbers.

## Next optimization pass

- Add Davidson warm starts from previous eigenvector.
- Cache selected-address gathers.
- Add optional diagonal EN2 denominator.
- Add block/parent-aware candidate masks.
- Add multiprocessing or numba-accelerated rank diagnostics.

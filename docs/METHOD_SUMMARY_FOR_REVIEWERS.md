# Method summary for reviewers

The primary v23 solver is a deterministic selected-CI solver in the fixed Cr2 CAS(12,12) active space.

1. Build PySCF CASSCF active-space integrals for Cr2 at R = 1.6788 Angstrom with cc-pVDZ.
2. Work in the fixed N_alpha = N_beta = 6 determinant sector.
3. Start from the reference determinant.
4. Apply PySCF `direct_spin1` Hamiltonian contractions directly in active-space integral form.
5. Score external candidates using an EN2-style coupling score.
6. Add high-scoring determinants to the selected subspace.
7. Diagonalize the selected Hamiltonian subspace.
8. Repeat until the gap to the active-space CASSCF reference is below the target.

The selected determinant score is not the final energy. The reported energy is variational and comes from selected-subspace diagonalization.

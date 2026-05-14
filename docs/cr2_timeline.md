# Cr2 timeline

## CAS(8,8), v14.16

- 16 qubits.
- Fixed-sector validation.
- E_var = -2086.493652 Ha.
- Gap = 0.271 mHa.
- Clean N/Sz/S2.

## CAS(10,10), v19 natural-orbital selected-CI

- 20 qubits, 14,251 Pauli terms.
- 8,176 determinants.
- E_var = -2086.6244525 Ha.
- Gap = 0.483 mHa.
- Decisive rank-10 event at step037 collapsed the gap from 2.207 mHa to 0.483 mHa.

## CAS(12,12), v21.3/v21.4b natural-orbital selected-CI

- 24 qubits.
- Natural-orbital selected-CI lineage.
- Active rotation provenance: `active_rotation:c65788197e7dc63e`.
- v38 paper snapshot: 16,026 determinants, E_var = -2086.649342 Ha, gap = 1.491 mHa.
- v21.4b restart is in progress and should replace this row if it reaches a lower verified variational gap.

## Important warning

Do not use continuation outputs that reinterpret the v14.35/v21.1 determinant vector in a non-natural-orbital Hamiltonian basis. Such runs may reproduce the stored restart energy initially but fail after the first actual diagonalization.

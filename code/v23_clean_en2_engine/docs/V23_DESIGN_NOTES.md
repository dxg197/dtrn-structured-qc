# v23 design notes

## Why EN2 scoring

v22 proved that the direct active-space contraction path is fast, but raw residual selection is determinant-inefficient. v23 uses an Epstein-Nesbet-like score:

```text
score_i = |r_i|^2 / |E_var - H_ii|
```

where:

```text
r_i = H_iS c_S
H_ii = diagonal determinant energy
```

This should prioritize determinants with both strong coupling and useful diagonal energy.

## Legitimacy

v23 is a variational selected-CI solver. The selected determinants are chosen heuristically, but the reported energy is the lowest eigenvalue of the Hamiltonian projected into the selected determinant subspace. Therefore `E_var` is a legitimate variational upper bound for the active-space Hamiltonian.

## What EN2 is not

The EN2/PT2 estimate is not the paper-safe energy. It is used for selection and diagnostics. Report `E_var` as the paper-safe value.

## Expected validation

- Confirm monotone `E_var`.
- Confirm the PySCF CASSCF reference in metadata.
- Compare v23 against v22 at equal dimension.
- If using an active rotation, record the rotation hash.
- Do not compare to legacy v21.3 determinant counts unless the active-space integral conventions are proven identical.

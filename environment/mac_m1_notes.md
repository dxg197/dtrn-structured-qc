# Apple M1 notes

The paper reports quantum-chemistry variational runs on an Apple M1 workstation with 16 GB RAM.

Recommended practice:

1. Use a clean Python/conda environment.
2. Keep Hamiltonian caches outside normal Git history.
3. Record exact engine commit/hash and Hamiltonian cache hash in every run manifest.
4. Treat PT2/EN2 as diagnostic only; paper-safe claims should use variational `E_var`.
5. For Cr2 CAS(12,12), preserve the natural-orbital active rotation provenance: `active_rotation:c65788197e7dc63e`.

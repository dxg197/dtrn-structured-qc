# Method overview

DTRN represents dense linear maps as Kronecker products of small SO(d) rotation factors, optionally coupled through cross-factor mixers and a dissipative bottleneck.

The central empirical design rule is:

> DTRN works when the tensor factorization is aligned with native problem geometry.

Examples:

- Vision: patch-lattice geometry and row/column mixing.
- Language modeling: selective FFN/adaptation use rather than wholesale transformer replacement.
- Quantum chemistry: orbital/spin grouping, sector-aware initialization, natural-orbital preconditioning, adaptive-rank selected-CI candidate generation.

Quantum-chemistry claims use variational energies `E_var`. PT2/EN2 quantities are selection diagnostics, not headline energies.

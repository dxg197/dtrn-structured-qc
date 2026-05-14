# Known failure modes

## Flat/global DTRN

Flat DTRN without domain geometry can fail catastrophically, e.g. MNIST collapse to 11.35%.

## Wholesale transformer replacement

Replacing attention and FFN pathways at once is unstable and lossy in small language-model settings. Selective FFN/adaptation use is the paper-safe claim.

## Chemistry basis mismatch

A selected determinant/coeff vector must be interpreted in the same orbital/Hamiltonian basis that generated it. For Cr2 CAS(12,12), preserve the v14.35/v21.1 natural-orbital active rotation:

```text
active_rotation:c65788197e7dc63e
```

A mismatch can appear to load correctly if the old restart energy is trusted, then fail on the first actual diagonalization.

## Non-monotone selected-CI continuation

For a valid variational selected-CI continuation that retains the old determinant subspace, `E_var` should not increase. Reject non-monotone continuations unless there is a clear, documented reason.

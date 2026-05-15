# v23 Python 3.9 bit_count compatibility patch

Your Apple/Xcode Python reports itself as 3.9.6 but raises:

```text
AttributeError: 'int' object has no attribute 'bit_count'
```

inside:

```text
cr2v23/sector.py
```

This patch replaces the `popcount()` helper with a Python-version-safe fallback and also speeds up `ranks_for_flat_indices()` by precomputing alpha and beta ranks separately.

## Install

From inside `Cr2_v23_clean_en2_engine`:

```bash
unzip Cr2_v23_py39_bitcount_patch.zip
./PATCH_V23_PY39_BITCOUNT.sh
```

## Retry

```bash
RUN=1 ./RUN_V23_FROM_ZERO_24H_EN2.sh
```

The existing `v23_cache/active_integrals_cr2_cas12.npz` is fine and does not need rebuilding.

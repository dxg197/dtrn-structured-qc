from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import re
import numpy as np

@dataclass
class SectorIndex:
    ncas: int
    nalpha: int
    nbeta: int
    alpha_strings: np.ndarray
    beta_strings: np.ndarray
    alpha_addr: dict[int, int]
    beta_addr: dict[int, int]

    @property
    def na(self) -> int:
        return len(self.alpha_strings)

    @property
    def nb(self) -> int:
        return len(self.beta_strings)

    @property
    def full_size(self) -> int:
        return self.na * self.nb

    def flat(self, ia: int, ib: int) -> int:
        return int(ia) * self.nb + int(ib)

    def unflat(self, idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        idx = np.asarray(idx, dtype=np.int64)
        return idx // self.nb, idx % self.nb

def make_sector(ncas: int, nelec: int | tuple[int, int]) -> SectorIndex:
    from pyscf.fci import cistring
    if isinstance(nelec, tuple):
        nalpha, nbeta = nelec
    else:
        nalpha = nelec // 2
        nbeta = nelec - nalpha
    alpha_strings = np.asarray(cistring.gen_strings4orblist(range(ncas), nalpha), dtype=np.int64)
    beta_strings = np.asarray(cistring.gen_strings4orblist(range(ncas), nbeta), dtype=np.int64)
    return SectorIndex(
        ncas=ncas,
        nalpha=nalpha,
        nbeta=nbeta,
        alpha_strings=alpha_strings,
        beta_strings=beta_strings,
        alpha_addr={int(s): i for i, s in enumerate(alpha_strings)},
        beta_addr={int(s): i for i, s in enumerate(beta_strings)},
    )

def hf_flat_index(sector: SectorIndex) -> int:
    alpha = (1 << sector.nalpha) - 1
    beta = (1 << sector.nbeta) - 1
    return sector.flat(sector.alpha_addr[alpha], sector.beta_addr[beta])

def popcount(x: int) -> int:
    """Python-version-safe population count.

    Some Apple/Xcode Python 3.9 builds do not expose int.bit_count().
    The CAS bitstrings here are non-negative and small, so bin().count("1")
    is safe and fast enough. For normal modern Python, use bit_count().
    """
    x = int(x)
    if x < 0:
        raise ValueError(f"popcount expected non-negative integer, got {x}")
    bc = getattr(x, "bit_count", None)
    if bc is not None:
        return int(bc())
    return bin(x).count("1")

def excitation_rank(alpha: int, beta: int, ref_alpha: int, ref_beta: int) -> int:
    return popcount(ref_alpha & ~alpha) + popcount(ref_beta & ~beta)

def ranks_for_flat_indices(sector: SectorIndex, flat: np.ndarray, ref_flat: int | None = None) -> np.ndarray:
    """Compute excitation-rank diagnostics for flat determinant indices.

    This version is compatible with Python builds that lack int.bit_count() and
    avoids a full Python loop over all 853,776 CAS(12,12) determinants by
    precomputing ranks separately for the 924 alpha and 924 beta strings.
    """
    flat = np.asarray(flat, dtype=np.int64)
    ia, ib = sector.unflat(flat)

    if ref_flat is None:
        ref_flat = hf_flat_index(sector)
    ria, rib = sector.unflat(np.asarray([ref_flat], dtype=np.int64))
    ref_a = int(sector.alpha_strings[int(ria[0])])
    ref_b = int(sector.beta_strings[int(rib[0])])

    alpha_rank = np.empty(sector.na, dtype=np.int16)
    beta_rank = np.empty(sector.nb, dtype=np.int16)

    for i, s in enumerate(sector.alpha_strings):
        alpha_rank[i] = popcount(ref_a & ~int(s))
    for i, s in enumerate(sector.beta_strings):
        beta_rank[i] = popcount(ref_b & ~int(s))

    return (alpha_rank[ia] + beta_rank[ib]).astype(np.int16)

def load_clean_restart(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    path = Path(path)
    pairs = path / "selected_pairs_final.npy"
    coeff = path / "selected_coeff_final.npy"
    if not pairs.exists() or not coeff.exists():
        raise FileNotFoundError(f"Expected clean restart files selected_pairs_final.npy and selected_coeff_final.npy in {path}")
    c = np.load(coeff)
    if np.iscomplexobj(c):
        idx = int(np.argmax(np.abs(c)))
        phase = np.exp(-1j * np.angle(c[idx])) if abs(c[idx]) > 0 else 1.0
        c = np.real(c * phase)
    c = np.asarray(c, dtype=np.float64)
    n = np.linalg.norm(c)
    if n <= 0:
        raise ValueError("restart coefficient norm is zero")
    return np.load(pairs).astype(np.int64), c / n

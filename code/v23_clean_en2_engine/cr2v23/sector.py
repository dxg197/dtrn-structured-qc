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
    return int(x).bit_count()

def excitation_rank(alpha: int, beta: int, ref_alpha: int, ref_beta: int) -> int:
    return popcount(ref_alpha & ~alpha) + popcount(ref_beta & ~beta)

def ranks_for_flat_indices(sector: SectorIndex, flat: np.ndarray, ref_flat: int | None = None) -> np.ndarray:
    flat = np.asarray(flat, dtype=np.int64)
    ia, ib = sector.unflat(flat)
    if ref_flat is None:
        ref_flat = hf_flat_index(sector)
    ria, rib = sector.unflat(np.asarray([ref_flat], dtype=np.int64))
    ref_a = int(sector.alpha_strings[int(ria[0])])
    ref_b = int(sector.beta_strings[int(rib[0])])
    out = np.empty(len(flat), dtype=np.int16)
    for k, (a, b) in enumerate(zip(ia, ib)):
        out[k] = excitation_rank(int(sector.alpha_strings[int(a)]), int(sector.beta_strings[int(b)]), ref_a, ref_b)
    return out

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

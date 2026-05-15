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

def legacy_spin_orbital_to_flat(
    dets: np.ndarray,
    sector: SectorIndex,
    layout: Literal["auto", "interleaved", "block"] = "auto",
) -> np.ndarray:
    dets = np.asarray(dets, dtype=np.uint64).reshape(-1)

    def convert(which: str):
        out = []
        bad = 0
        for d0 in dets:
            d = int(d0)
            a = 0
            b = 0
            if which == "interleaved":
                for i in range(sector.ncas):
                    if d & (1 << (2 * i)):
                        a |= 1 << i
                    if d & (1 << (2 * i + 1)):
                        b |= 1 << i
            elif which == "block":
                for i in range(sector.ncas):
                    if d & (1 << i):
                        a |= 1 << i
                    if d & (1 << (sector.ncas + i)):
                        b |= 1 << i
            else:
                raise ValueError(which)
            ia = sector.alpha_addr.get(a)
            ib = sector.beta_addr.get(b)
            if ia is None or ib is None:
                bad += 1
                out.append(-1)
            else:
                out.append(sector.flat(ia, ib))
        return np.asarray(out, dtype=np.int64), bad

    if layout == "auto":
        cands = []
        for which in ("interleaved", "block"):
            arr, bad = convert(which)
            cands.append((bad, which, arr))
        cands.sort(key=lambda x: x[0])
        bad, which, arr = cands[0]
        if bad:
            raise ValueError(f"Could not map all legacy determinants. Best layout={which}, bad={bad}/{len(dets)}")
        print(f"[legacy import] auto-selected spin layout: {which}")
        return arr

    arr, bad = convert(layout)
    if bad:
        raise ValueError(f"layout={layout} failed for {bad}/{len(dets)} determinants")
    return arr

def load_restart_from_directory(path: str | Path, sector: SectorIndex, legacy_layout: str = "auto") -> tuple[np.ndarray, np.ndarray]:
    path = Path(path)
    pairs = path / "selected_pairs_final.npy"
    coeff = path / "selected_coeff_final.npy"
    if pairs.exists() and coeff.exists():
        return np.load(pairs).astype(np.int64), np.load(coeff).astype(np.float64)

    det_candidates = sorted(path.glob("selected_dets_final*.npy"))
    coeff_candidates = sorted(path.glob("selected_coeff_final*.npy"))
    if not det_candidates:
        det_candidates = sorted(path.glob("selected_dets_iter*_dim*.npy"))
    if not coeff_candidates:
        coeff_candidates = sorted(path.glob("selected_coeff_iter*_dim*.npy"))
    if not det_candidates or not coeff_candidates:
        raise FileNotFoundError(f"Could not find selected det/coeff files in {path}")

    def last_number(p: Path) -> int:
        nums = [int(x) for x in re.findall(r"\d+", p.name)]
        return nums[-1] if nums else -1

    det_file = sorted(det_candidates, key=last_number)[-1]
    coeff_file = sorted(coeff_candidates, key=last_number)[-1]
    print(f"[restart] det_file={det_file}")
    print(f"[restart] coeff_file={coeff_file}")
    flat = legacy_spin_orbital_to_flat(np.load(det_file), sector, layout=legacy_layout)
    coeffs = np.load(coeff_file).astype(np.float64)
    return flat, coeffs

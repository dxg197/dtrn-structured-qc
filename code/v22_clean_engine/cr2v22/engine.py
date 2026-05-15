from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import csv
import time

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

from .integrals import load_integrals
from .sector import SectorIndex, hf_flat_index, ranks_for_flat_indices, make_sector
from .utils import gap_mha, write_json

@dataclass
class EngineConfig:
    integrals: Path
    output_dir: Path
    target_gap_mha: float = 0.5
    max_dim: int = 30000
    walltime_seconds: int = 86400
    add_per_iter: int = 500
    max_iters: int = 100
    candidate_limit: int = 200000
    rank_filter: int = 12
    plateau_gain_per_kdet: float = 0.05
    unlock_rank: int = 12
    eig_tol: float = 1e-8
    eig_maxiter: int = 300
    legacy_layout: str = "auto"
    restart_dir: Optional[Path] = None

class CleanSelectedCI:
    def __init__(self, cfg: EngineConfig):
        self.cfg = cfg
        self.cfg.output_dir.mkdir(parents=True, exist_ok=True)
        h1e, eri, ecore, e_ref, ncas, nelecas = load_integrals(cfg.integrals)
        self.h1e = h1e
        self.eri = eri
        self.ecore = float(ecore)
        self.e_ref = float(e_ref)
        self.ncas = int(ncas)
        self.nelecas = int(nelecas)
        self.sector = make_sector(self.ncas, self.nelecas)
        from pyscf.fci import direct_spin1
        self.direct_spin1 = direct_spin1
        self.h2e = direct_spin1.absorb_h1e(self.h1e, self.eri, self.ncas, self.nelecas, 0.5)
        self.selected: np.ndarray
        self.coeff: np.ndarray
        self.energy: float

    def scatter(self, vec_selected: np.ndarray, selected: Optional[np.ndarray] = None) -> np.ndarray:
        selected = self.selected if selected is None else selected
        full = np.zeros((self.sector.na, self.sector.nb), dtype=np.float64)
        ia, ib = self.sector.unflat(selected)
        full[ia, ib] = vec_selected
        return full

    def gather(self, full: np.ndarray, selected: Optional[np.ndarray] = None) -> np.ndarray:
        selected = self.selected if selected is None else selected
        ia, ib = self.sector.unflat(selected)
        return np.asarray(full[ia, ib], dtype=np.float64)

    def contract_full(self, ci_full: np.ndarray) -> np.ndarray:
        sigma = self.direct_spin1.contract_2e(self.h2e, ci_full, self.ncas, self.nelecas)
        return sigma + self.ecore * ci_full

    def initialize(self, restart_dir: Optional[Path] = None, legacy_layout: str = "auto") -> None:
        if restart_dir is None:
            self.selected = np.asarray([hf_flat_index(self.sector)], dtype=np.int64)
            self.coeff = np.asarray([1.0], dtype=np.float64)
            self.energy = self.rayleigh(self.selected, self.coeff)
            return
        from .sector import load_restart_from_directory
        flat, coeff = load_restart_from_directory(restart_dir, self.sector, legacy_layout=legacy_layout)
        order = np.argsort(flat)
        flat_s = flat[order]
        coeff_s = coeff[order]
        uniq, idx = np.unique(flat_s, return_index=True)
        cuniq = np.zeros_like(uniq, dtype=np.float64)
        for i, start in enumerate(idx):
            end = idx[i + 1] if i + 1 < len(idx) else len(flat_s)
            cuniq[i] = coeff_s[start:end].sum()
        norm = np.linalg.norm(cuniq)
        if norm <= 0:
            raise ValueError("restart coefficient norm is zero")
        self.selected = uniq.astype(np.int64)
        self.coeff = cuniq / norm
        self.energy = self.rayleigh(self.selected, self.coeff)

    def rayleigh(self, selected: np.ndarray, coeff: np.ndarray) -> float:
        full = np.zeros((self.sector.na, self.sector.nb), dtype=np.float64)
        ia, ib = self.sector.unflat(selected)
        full[ia, ib] = coeff
        sigma = self.contract_full(full)
        return float(np.dot(coeff, sigma[ia, ib]))

    def solve_selected(self) -> tuple[float, np.ndarray]:
        n = len(self.selected)
        def mv(x):
            full = self.scatter(np.asarray(x, dtype=np.float64))
            sigma = self.contract_full(full)
            return self.gather(sigma)
        op = LinearOperator((n, n), matvec=mv, dtype=np.float64)
        if n == 1:
            e = float(mv(np.ones(1))[0])
            return e, np.ones(1)
        vals, vecs = eigsh(op, k=1, which="SA", tol=self.cfg.eig_tol, maxiter=self.cfg.eig_maxiter)
        coeff = vecs[:, 0]
        coeff = coeff / np.linalg.norm(coeff)
        return float(vals[0]), coeff

    def residual_scores(self) -> tuple[np.ndarray, np.ndarray]:
        full = self.scatter(self.coeff)
        sigma = self.contract_full(full)
        ia, ib = self.sector.unflat(self.selected)
        sigma[ia, ib] = 0.0
        scores = np.abs(sigma.reshape(-1))
        scores[self.selected] = 0.0
        if self.cfg.rank_filter is not None and self.cfg.rank_filter < self.ncas:
            flat_all = np.arange(self.sector.full_size, dtype=np.int64)
            ranks = ranks_for_flat_indices(self.sector, flat_all)
            scores[ranks > self.cfg.rank_filter] = 0.0
        positive = np.count_nonzero(scores)
        if positive == 0:
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.float64)
        limit = min(int(self.cfg.candidate_limit), positive)
        idx = np.argpartition(scores, -limit)[-limit:]
        idx = idx[np.argsort(scores[idx])[::-1]]
        return idx.astype(np.int64), scores[idx].astype(np.float64)

    def add_candidates(self, add_n: int) -> tuple[int, dict]:
        idx, scores = self.residual_scores()
        if len(idx) == 0:
            return 0, {"reason": "no positive residual candidates"}
        new = idx[:add_n]
        before = len(self.selected)
        self.selected = np.unique(np.concatenate([self.selected, new])).astype(np.int64)
        added = len(self.selected) - before
        return added, {"top_score": float(scores[0]) if len(scores) else 0.0, "candidate_count": int(len(idx))}

    def save_checkpoint(self, tag: str, diagnostics: dict):
        out = self.cfg.output_dir
        np.save(out / "selected_pairs_final.npy", self.selected)
        np.save(out / "selected_coeff_final.npy", self.coeff)
        ia, ib = self.sector.unflat(self.selected)
        top = np.argsort(np.abs(self.coeff))[::-1][:100]
        with (out / "top_determinants_final.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "flat_index", "alpha_addr", "beta_addr", "alpha_string", "beta_string", "coeff_abs", "coeff"])
            for rank, j in enumerate(top, 1):
                jj = int(j)
                w.writerow([rank, int(self.selected[jj]), int(ia[jj]), int(ib[jj]), int(self.sector.alpha_strings[int(ia[jj])]), int(self.sector.beta_strings[int(ib[jj])]), abs(float(self.coeff[jj])), float(self.coeff[jj])])
        summary = {
            "schema": "cr2v22_clean_checkpoint_v1",
            "tag": tag,
            "selected_dim": int(len(self.selected)),
            "E_var": float(self.energy),
            "E_ref": float(self.e_ref),
            "gap_mHa": float(gap_mha(self.energy, self.e_ref)),
            "ncas": self.ncas,
            "nelecas": self.nelecas,
            "full_sector_size": int(self.sector.full_size),
            "engine": "clean_full_sector_residual_selected_ci",
            "hamiltonian": "PySCF active-space integrals; direct_spin1 contraction; no Pauli cache",
            "diagnostics": diagnostics,
        }
        write_json(out / "cr2_v22_clean_final.json", summary)

    def run(self) -> dict:
        t0 = time.time()
        self.initialize(self.cfg.restart_dir, legacy_layout=self.cfg.legacy_layout)
        print(f"[clean-v22] full sector size={self.sector.full_size} alpha={self.sector.na} beta={self.sector.nb}")
        print(f"[clean-v22] start_dim={len(self.selected)} E={self.energy:.16f} gap={gap_mha(self.energy, self.e_ref):.12f} mHa")
        progress_path = self.cfg.output_dir / "progress.csv"
        with progress_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["iter", "selected_dim", "E_var", "gap_mHa", "added", "gain_mHa", "gain_per_kdet", "candidate_count", "top_score", "wall_seconds"])
        last_energy = self.energy
        last_gap = gap_mha(self.energy, self.e_ref)
        recent = []
        for it in range(self.cfg.max_iters):
            if time.time() - t0 > self.cfg.walltime_seconds:
                print("[clean-v22] walltime reached")
                break
            if last_gap <= self.cfg.target_gap_mha:
                print("[clean-v22] target reached")
                break
            if len(self.selected) >= self.cfg.max_dim:
                print("[clean-v22] max dim reached")
                break
            if len(recent) >= 2 and all(x < self.cfg.plateau_gain_per_kdet for x in recent[-2:]):
                old_rank = self.cfg.rank_filter
                self.cfg.rank_filter = self.cfg.unlock_rank
                print(f"[clean-v22] plateau: raising rank_filter {old_rank} -> {self.cfg.rank_filter}")
            add_n = min(self.cfg.add_per_iter, self.cfg.max_dim - len(self.selected))
            added, diag = self.add_candidates(add_n)
            if added == 0:
                print(f"[clean-v22] no candidates added: {diag}")
                break
            e, coeff = self.solve_selected()
            if e > last_energy + 1e-10:
                raise RuntimeError(f"Non-monotone E_var: old={last_energy:.16f}, new={e:.16f}")
            self.energy = e
            self.coeff = coeff
            gap = gap_mha(e, self.e_ref)
            gain = last_gap - gap
            gain_per_kdet = gain / max(added / 1000.0, 1e-12)
            recent.append(gain_per_kdet)
            print(f"[clean-v22] iter={it} dim={len(self.selected)} E={e:.16f} gap={gap:.12f} added={added} gain/kdet={gain_per_kdet:.6f}")
            with progress_path.open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow([it, len(self.selected), f"{e:.16f}", f"{gap:.12f}", added, f"{gain:.12f}", f"{gain_per_kdet:.12f}", diag.get("candidate_count", ""), diag.get("top_score", ""), f"{time.time() - t0:.3f}"])
            self.save_checkpoint(f"iter{it:03d}", {"last_add": diag, "gain_per_kdet": gain_per_kdet})
            last_energy = e
            last_gap = gap
        self.save_checkpoint("final", {"wall_seconds": time.time() - t0})
        return {"selected_dim": int(len(self.selected)), "E_var": float(self.energy), "E_ref": float(self.e_ref), "gap_mHa": float(gap_mha(self.energy, self.e_ref)), "output_dir": str(self.cfg.output_dir)}

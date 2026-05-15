from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import csv
import time

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

from .integrals import load_integrals
from .sector import SectorIndex, hf_flat_index, ranks_for_flat_indices, make_sector, load_clean_restart
from .utils import gap_mha, write_json

@dataclass
class EngineConfig:
    integrals: Path
    output_dir: Path
    target_gap_mha: float = 0.5
    max_dim: int = 120000
    walltime_seconds: int = 86400
    add_per_iter: int = 1000
    max_iters: int = 200
    candidate_limit: int = 853776
    rank_filter: int = 12
    plateau_gain_per_kdet: float = 0.05
    unlock_rank: int = 12
    eig_tol: float = 1e-8
    eig_maxiter: int = 300
    restart_dir: Optional[Path] = None

    score_mode: str = "en2"  # en2, residual, hybrid
    denom_floor: float = 1e-8
    hybrid_residual_weight: float = 0.05
    min_abs_residual: float = 0.0
    diagnostic_top_k: int = 20

class CleanEN2SelectedCI:
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
        self.hdiag = np.asarray(direct_spin1.make_hdiag(self.h1e, self.eri, self.ncas, self.nelecas), dtype=np.float64)
        self.hdiag = self.hdiag.reshape(-1) + self.ecore

        self.full_indices = np.arange(self.sector.full_size, dtype=np.int64)
        self.rank_cache = ranks_for_flat_indices(self.sector, self.full_indices)

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

    def initialize(self, restart_dir: Optional[Path] = None) -> None:
        if restart_dir is None:
            self.selected = np.asarray([hf_flat_index(self.sector)], dtype=np.int64)
            self.coeff = np.asarray([1.0], dtype=np.float64)
            self.energy = self.rayleigh(self.selected, self.coeff)
            return
        flat, coeff = load_clean_restart(restart_dir)
        flat = np.asarray(flat, dtype=np.int64)
        coeff = np.asarray(coeff, dtype=np.float64)
        order = np.argsort(flat)
        flat = flat[order]
        coeff = coeff[order]
        uniq, idx = np.unique(flat, return_index=True)
        cuniq = np.zeros(len(uniq), dtype=np.float64)
        for i, start in enumerate(idx):
            end = idx[i + 1] if i + 1 < len(idx) else len(flat)
            cuniq[i] = coeff[start:end].sum()
        n = np.linalg.norm(cuniq)
        if n <= 0:
            raise ValueError("restart coefficient norm is zero after dedup")
        self.selected = uniq
        self.coeff = cuniq / n
        self.energy = self.rayleigh(self.selected, self.coeff)

    def rayleigh(self, selected: np.ndarray, coeff: np.ndarray) -> float:
        full = np.zeros((self.sector.na, self.sector.nb), dtype=np.float64)
        ia, ib = self.sector.unflat(selected)
        full[ia, ib] = coeff
        sigma = self.contract_full(full)
        return float(np.dot(coeff, sigma[ia, ib]))

    def solve_selected(self, v0: Optional[np.ndarray] = None) -> tuple[float, np.ndarray]:
        n = len(self.selected)
        def mv(x):
            full = self.scatter(np.asarray(x, dtype=np.float64))
            sigma = self.contract_full(full)
            return self.gather(sigma)
        op = LinearOperator((n, n), matvec=mv, dtype=np.float64)
        if n == 1:
            e = float(mv(np.ones(1))[0])
            return e, np.ones(1)
        if v0 is not None:
            v0 = np.asarray(v0, dtype=np.float64)
            norm = np.linalg.norm(v0)
            if len(v0) != n or norm <= 0:
                v0 = None
            else:
                v0 = v0 / norm
        vals, vecs = eigsh(op, k=1, which="SA", tol=self.cfg.eig_tol, maxiter=self.cfg.eig_maxiter, v0=v0)
        coeff = vecs[:, 0]
        coeff = coeff / np.linalg.norm(coeff)
        return float(vals[0]), coeff

    def external_residual(self) -> np.ndarray:
        full = self.scatter(self.coeff)
        sigma = self.contract_full(full)
        residual = sigma.reshape(-1)
        residual = np.asarray(residual, dtype=np.float64)
        residual[self.selected] = 0.0
        return residual

    def score_candidates(self) -> tuple[np.ndarray, dict]:
        residual = self.external_residual()
        abs_r = np.abs(residual)
        if self.cfg.min_abs_residual > 0:
            abs_r[abs_r < self.cfg.min_abs_residual] = 0.0

        denom_signed = self.energy - self.hdiag
        denom_abs = np.maximum(np.abs(denom_signed), self.cfg.denom_floor)

        if self.cfg.score_mode == "residual":
            scores = abs_r
        elif self.cfg.score_mode == "en2":
            scores = (abs_r * abs_r) / denom_abs
        elif self.cfg.score_mode == "hybrid":
            en2 = (abs_r * abs_r) / denom_abs
            if np.max(abs_r) > 0 and np.max(en2) > 0:
                scores = en2 / np.max(en2) + self.cfg.hybrid_residual_weight * (abs_r / np.max(abs_r))
            else:
                scores = en2
        else:
            raise ValueError(f"unknown score_mode: {self.cfg.score_mode}")

        scores[self.selected] = 0.0
        if self.cfg.rank_filter is not None and self.cfg.rank_filter < self.ncas:
            scores[self.rank_cache > self.cfg.rank_filter] = 0.0

        positive = np.count_nonzero(scores)
        if positive == 0:
            return np.empty(0, dtype=np.int64), {"candidate_count": 0}

        limit = min(int(self.cfg.candidate_limit), positive)
        idx = np.argpartition(scores, -limit)[-limit:]
        idx = idx[np.argsort(scores[idx])[::-1]]

        # Diagnostic PT2 over the selected candidate list and all nonzero scores.
        top = idx[: min(self.cfg.diagnostic_top_k, len(idx))]
        pt2_top = np.sum((residual[top] * residual[top]) / np.where(np.abs(denom_signed[top]) < self.cfg.denom_floor, -self.cfg.denom_floor, denom_signed[top]))
        selected_for_pt2 = idx
        pt2_pool = np.sum((residual[selected_for_pt2] * residual[selected_for_pt2]) / np.where(np.abs(denom_signed[selected_for_pt2]) < self.cfg.denom_floor, -self.cfg.denom_floor, denom_signed[selected_for_pt2]))

        diag = {
            "candidate_count": int(len(idx)),
            "positive_score_count": int(positive),
            "top_score": float(scores[idx[0]]),
            "top_abs_residual": float(abs_r[idx[0]]),
            "top_hdiag": float(self.hdiag[idx[0]]),
            "top_denom_signed": float(denom_signed[idx[0]]),
            "pt2_top_Ha": float(pt2_top),
            "pt2_pool_Ha": float(pt2_pool),
            "score_mode": self.cfg.score_mode,
        }
        return idx.astype(np.int64), diag

    def add_candidates(self, add_n: int) -> tuple[int, np.ndarray, dict]:
        old_selected = self.selected.copy()
        old_coeff = self.coeff.copy()
        idx, diag = self.score_candidates()
        if len(idx) == 0:
            return 0, np.zeros_like(self.selected, dtype=np.float64), diag
        new = idx[:add_n]
        combined = np.unique(np.concatenate([self.selected, new])).astype(np.int64)
        added = len(combined) - len(self.selected)

        # Warm-start old vector in new sorted basis.
        pos = {int(v): i for i, v in enumerate(combined)}
        v0 = np.zeros(len(combined), dtype=np.float64)
        for old_i, det in enumerate(old_selected):
            v0[pos[int(det)]] = old_coeff[old_i]

        self.selected = combined
        return added, v0, diag

    def save_checkpoint(self, tag: str, diagnostics: dict):
        out = self.cfg.output_dir
        np.save(out / "selected_pairs_final.npy", self.selected)
        np.save(out / "selected_coeff_final.npy", self.coeff)

        ia, ib = self.sector.unflat(self.selected)
        top = np.argsort(np.abs(self.coeff))[::-1][:100]
        with (out / "top_determinants_final.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "flat_index", "alpha_addr", "beta_addr", "alpha_string", "beta_string", "excitation_rank", "coeff_abs", "coeff", "Hii"])
            for rank, j in enumerate(top, 1):
                jj = int(j)
                flat = int(self.selected[jj])
                w.writerow([
                    rank,
                    flat,
                    int(ia[jj]),
                    int(ib[jj]),
                    int(self.sector.alpha_strings[int(ia[jj])]),
                    int(self.sector.beta_strings[int(ib[jj])]),
                    int(self.rank_cache[flat]),
                    abs(float(self.coeff[jj])),
                    float(self.coeff[jj]),
                    float(self.hdiag[flat]),
                ])

        summary = {
            "schema": "cr2v23_clean_en2_checkpoint_v1",
            "tag": tag,
            "selected_dim": int(len(self.selected)),
            "E_var": float(self.energy),
            "E_ref": float(self.e_ref),
            "gap_mHa": float(gap_mha(self.energy, self.e_ref)),
            "ncas": self.ncas,
            "nelecas": self.nelecas,
            "full_sector_size": int(self.sector.full_size),
            "engine": "clean_full_sector_en2_selected_ci",
            "hamiltonian": "PySCF active-space integrals; direct_spin1 contraction; no Pauli cache",
            "score_mode": self.cfg.score_mode,
            "denom_floor": self.cfg.denom_floor,
            "diagnostics": diagnostics,
        }
        write_json(out / "cr2_v23_clean_final.json", summary)

    def run(self) -> dict:
        t0 = time.time()
        self.initialize(self.cfg.restart_dir)
        print(f"[v23] full sector size={self.sector.full_size} alpha={self.sector.na} beta={self.sector.nb}")
        print(f"[v23] hdiag range=[{self.hdiag.min():.6f}, {self.hdiag.max():.6f}]")
        print(f"[v23] start_dim={len(self.selected)} E={self.energy:.16f} gap={gap_mha(self.energy, self.e_ref):.12f} mHa score_mode={self.cfg.score_mode}")

        progress_path = self.cfg.output_dir / "progress.csv"
        with progress_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "iter", "selected_dim", "E_var", "gap_mHa", "added", "gain_mHa", "gain_per_kdet",
                "candidate_count", "top_score", "top_abs_residual", "top_denom_signed", "pt2_pool_Ha", "wall_seconds"
            ])

        last_energy = self.energy
        last_gap = gap_mha(self.energy, self.e_ref)
        recent = []

        for it in range(self.cfg.max_iters):
            if time.time() - t0 > self.cfg.walltime_seconds:
                print("[v23] walltime reached")
                break
            if last_gap <= self.cfg.target_gap_mha:
                print("[v23] target reached")
                break
            if len(self.selected) >= self.cfg.max_dim:
                print("[v23] max dim reached")
                break

            if len(recent) >= 2 and all(x < self.cfg.plateau_gain_per_kdet for x in recent[-2:]):
                old_rank = self.cfg.rank_filter
                self.cfg.rank_filter = self.cfg.unlock_rank
                print(f"[v23] plateau: rank_filter {old_rank} -> {self.cfg.rank_filter}")

            add_n = min(self.cfg.add_per_iter, self.cfg.max_dim - len(self.selected))
            added, v0, diag = self.add_candidates(add_n)
            if added == 0:
                print(f"[v23] no candidates added: {diag}")
                break

            e, coeff = self.solve_selected(v0=v0)
            if e > last_energy + 1e-10:
                raise RuntimeError(f"Non-monotone E_var: old={last_energy:.16f}, new={e:.16f}")

            self.energy = e
            self.coeff = coeff
            gap = gap_mha(e, self.e_ref)
            gain = last_gap - gap
            gain_per_kdet = gain / max(added / 1000.0, 1e-12)
            recent.append(gain_per_kdet)

            print(
                f"[v23] iter={it} dim={len(self.selected)} E={e:.16f} gap={gap:.12f} "
                f"added={added} gain/kdet={gain_per_kdet:.6f} pt2_pool={diag.get('pt2_pool_Ha', 0.0):.6e}"
            )

            with progress_path.open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow([
                    it,
                    len(self.selected),
                    f"{e:.16f}",
                    f"{gap:.12f}",
                    added,
                    f"{gain:.12f}",
                    f"{gain_per_kdet:.12f}",
                    diag.get("candidate_count", ""),
                    diag.get("top_score", ""),
                    diag.get("top_abs_residual", ""),
                    diag.get("top_denom_signed", ""),
                    diag.get("pt2_pool_Ha", ""),
                    f"{time.time() - t0:.3f}",
                ])

            self.save_checkpoint(f"iter{it:03d}", {"last_add": diag, "gain_per_kdet": gain_per_kdet})
            last_energy = e
            last_gap = gap

        self.save_checkpoint("final", {"wall_seconds": time.time() - t0})
        return {
            "selected_dim": int(len(self.selected)),
            "E_var": float(self.energy),
            "E_ref": float(self.e_ref),
            "gap_mHa": float(gap_mha(self.energy, self.e_ref)),
            "output_dir": str(self.cfg.output_dir),
        }

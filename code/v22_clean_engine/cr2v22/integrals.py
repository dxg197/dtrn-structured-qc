from __future__ import annotations

from pathlib import Path
import time
import numpy as np
from .utils import write_json, sha256_file

def build_cr2_cas12_integrals(
    output_dir: str | Path,
    bond_angstrom: float = 1.6788,
    basis: str = "cc-pvdz",
    ncas: int = 12,
    nelecas: int = 12,
    spin: int = 0,
    active_rotation: str | Path | None = None,
    force: bool = False,
) -> Path:
    # Build Cr2 CAS active-space integrals with PySCF.
    from pyscf import gto, scf, mcscf, ao2mo

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "active_integrals_cr2_cas12.npz"
    meta_path = output_dir / "active_integrals_cr2_cas12.meta.json"
    if out.exists() and meta_path.exists() and not force:
        return out

    t0 = time.time()
    atom = f"Cr 0 0 0; Cr 0 0 {bond_angstrom}"
    mol = gto.M(atom=atom, basis=basis, spin=spin, symmetry=False, verbose=4)
    mf = scf.RHF(mol)
    e_hf = mf.kernel()

    mc = mcscf.CASSCF(mf, ncas, nelecas)
    e_casscf = mc.kernel()[0]

    mo = mc.mo_coeff.copy()
    ncore = mc.ncore
    active_slice = slice(ncore, ncore + ncas)

    rotation_hash = None
    rotation_path = None
    if active_rotation is not None:
        active_rotation = Path(active_rotation)
        if not active_rotation.exists():
            raise FileNotFoundError(f"active rotation not found: {active_rotation}")
        rot = np.load(active_rotation)
        if rot.shape != (ncas, ncas):
            raise ValueError(f"active rotation shape {rot.shape} != {(ncas, ncas)}")
        mo[:, active_slice] = mo[:, active_slice] @ rot
        rotation_hash = sha256_file(active_rotation)
        rotation_path = str(active_rotation)

    h1e, ecore = mc.get_h1eff(mo_coeff=mo)
    eri = ao2mo.kernel(mol, mo[:, active_slice], compact=False)
    eri = eri.reshape(ncas, ncas, ncas, ncas)

    np.savez_compressed(
        out,
        h1e=h1e,
        eri=eri,
        ecore=np.array(ecore),
        e_hf=np.array(e_hf),
        e_ref=np.array(e_casscf),
        mo_coeff=mo,
        ncas=np.array(ncas),
        nelecas=np.array(nelecas),
        bond_angstrom=np.array(bond_angstrom),
    )

    meta = {
        "schema": "cr2v22_active_integrals_v1",
        "atom": atom,
        "basis": basis,
        "spin": spin,
        "ncas": ncas,
        "nelecas": nelecas,
        "ncore": int(ncore),
        "E_HF": float(e_hf),
        "E_CASSCF": float(e_casscf),
        "ecore": float(ecore),
        "active_rotation_path": rotation_path,
        "active_rotation_sha256": rotation_hash,
        "wall_seconds": time.time() - t0,
        "note": "Clean v22 uses active-space integrals and PySCF direct_spin1, not JW Pauli term caches.",
    }
    write_json(meta_path, meta)
    return out

def load_integrals(path: str | Path):
    data = np.load(path, allow_pickle=False)
    h1e = np.array(data["h1e"])
    eri = np.array(data["eri"])
    ecore = float(data["ecore"])
    e_ref = float(data["e_ref"])
    ncas = int(data["ncas"])
    nelecas = int(data["nelecas"])
    return h1e, eri, ecore, e_ref, ncas, nelecas

from __future__ import annotations

import argparse
from pathlib import Path
from .integrals import build_cr2_cas12_integrals
from .engine import CleanSelectedCI, EngineConfig
from .utils import write_json

def cmd_build_integrals(args):
    out = build_cr2_cas12_integrals(
        args.output_dir,
        bond_angstrom=args.bond,
        basis=args.basis,
        ncas=args.ncas,
        nelecas=args.nelecas,
        active_rotation=args.active_rotation,
        force=args.force,
    )
    print(out)

def cmd_run(args):
    cfg = EngineConfig(
        integrals=Path(args.integrals),
        output_dir=Path(args.output_dir),
        target_gap_mha=args.target_gap_mha,
        max_dim=args.max_dim,
        walltime_seconds=args.walltime_seconds,
        add_per_iter=args.add_per_iter,
        max_iters=args.max_iters,
        candidate_limit=args.candidate_limit,
        rank_filter=args.rank_filter,
        plateau_gain_per_kdet=args.plateau_gain_per_kdet,
        unlock_rank=args.unlock_rank,
        eig_tol=args.eig_tol,
        eig_maxiter=args.eig_maxiter,
        restart_dir=Path(args.restart_dir) if args.restart_dir else None,
        legacy_layout=args.legacy_layout,
    )
    eng = CleanSelectedCI(cfg)
    result = eng.run()
    write_json(Path(args.output_dir) / "run_result.json", result)
    print(result)

def main(argv=None):
    p = argparse.ArgumentParser(prog="cr2v22-clean")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-integrals")
    b.add_argument("--output-dir", default="v22_clean_cache")
    b.add_argument("--bond", type=float, default=1.6788)
    b.add_argument("--basis", default="cc-pvdz")
    b.add_argument("--ncas", type=int, default=12)
    b.add_argument("--nelecas", type=int, default=12)
    b.add_argument("--active-rotation", default=None)
    b.add_argument("--force", action="store_true")
    b.set_defaults(func=cmd_build_integrals)
    r = sub.add_parser("run-selected-ci")
    r.add_argument("--integrals", required=True)
    r.add_argument("--output-dir", required=True)
    r.add_argument("--restart-dir", default="")
    r.add_argument("--legacy-layout", default="auto", choices=["auto", "interleaved", "block"])
    r.add_argument("--target-gap-mha", type=float, default=0.5)
    r.add_argument("--max-dim", type=int, default=30000)
    r.add_argument("--walltime-seconds", type=int, default=86400)
    r.add_argument("--add-per-iter", type=int, default=500)
    r.add_argument("--max-iters", type=int, default=100)
    r.add_argument("--candidate-limit", type=int, default=200000)
    r.add_argument("--rank-filter", type=int, default=12)
    r.add_argument("--plateau-gain-per-kdet", type=float, default=0.05)
    r.add_argument("--unlock-rank", type=int, default=12)
    r.add_argument("--eig-tol", type=float, default=1e-8)
    r.add_argument("--eig-maxiter", type=int, default=300)
    r.set_defaults(func=cmd_run)
    args = p.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()

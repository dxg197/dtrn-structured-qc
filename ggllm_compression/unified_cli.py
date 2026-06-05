from __future__ import annotations

import argparse
from typing import List, Optional

from .benchmark_cli import main as ingest_main
from .compare import compare_ingests, load_ingest, write_comparison
from .dtrn_replacement import build_dtrn_replacement_report, write_dtrn_replacement_report
from .quantization_report import build_quantization_report, load_ingest as load_quant_ingest, write_quantization_report
from .recommend import build_recommendations, write_recommendations
from .report import write_pilot_report

VERSION = "0.4.3"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ggllm-opt", description="GG-LLM Optimizer v0.4.3")
    p.add_argument("--version", action="store_true")
    sub = p.add_subparsers(dest="cmd")

    ib = sub.add_parser("ingest-bench", help="ingest CSV/JSON benchmark logs")
    ib.add_argument("--input", action="append", required=True)
    ib.add_argument("--out-json", default="runs/benchmark_ingest_v0_4.json")
    ib.add_argument("--out-md", default="runs/benchmark_ingest_v0_4.md")

    rec = sub.add_parser("recommend", help="generate route/runtime recommendations")
    rec.add_argument("--profile", required=True)
    rec.add_argument("--bench")
    rec.add_argument("--mode", choices=["balanced", "cost", "latency", "quality"], default="balanced")
    rec.add_argument("--out-json", default="runs/recommendations_v0_4.json")
    rec.add_argument("--out-md", default="runs/recommendations_v0_4.md")

    cmp_p = sub.add_parser("compare", help="compare baseline and optimized benchmark ingests")
    cmp_p.add_argument("--baseline", required=True)
    cmp_p.add_argument("--optimized", required=True)
    cmp_p.add_argument("--out-json", default="runs/comparison_v0_4.json")
    cmp_p.add_argument("--out-md", default="runs/comparison_v0_4.md")

    qc = sub.add_parser("quant-compare", help="compare quantization routes inside one ingested benchmark set")
    qc.add_argument("--bench", required=True, help="benchmark ingest JSON produced by ingest-bench")
    qc.add_argument("--baseline-quantization", default="native_mixed")
    qc.add_argument("--out-json", default="runs/quantization_comparison_v0_4.json")
    qc.add_argument("--out-md", default="runs/quantization_comparison_v0_4.md")

    dtrn = sub.add_parser("dtrn-scout", help="find DTRN replacement candidates with >=10% parameter reduction and no measured regression")
    dtrn.add_argument("--candidates", required=True, help="JSON file with module replacement candidates and baseline/candidate metrics")
    dtrn.add_argument("--min-param-reduction-pct", type=float, default=10.0)
    dtrn.add_argument("--tolerance", type=float, default=0.0, help="numeric tolerance for no-regression comparisons")
    dtrn.add_argument("--out-json", default="runs/dtrn_replacement_scout_v0_4_3.json")
    dtrn.add_argument("--out-md", default="runs/dtrn_replacement_scout_v0_4_3.md")

    rep = sub.add_parser("report", help="write pilot report")
    rep.add_argument("--profile", required=True)
    rep.add_argument("--baseline", required=True)
    rep.add_argument("--optimized")
    rep.add_argument("--recommendations")
    rep.add_argument("--comparison")
    rep.add_argument("--out-md", default="runs/pilot_report_v0_4.md")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(VERSION)
        return 0
    if args.cmd == "ingest-bench":
        cmd: List[str] = []
        for path in args.input:
            cmd += ["--input", path]
        cmd += ["--out-json", args.out_json, "--out-md", args.out_md]
        return ingest_main(cmd)
    if args.cmd == "recommend":
        data = build_recommendations(args.profile, bench_path=args.bench, mode=args.mode)
        write_recommendations(data, args.out_json, args.out_md)
        print(f"[ggllm-opt v{VERSION}] wrote {args.out_json} and {args.out_md}")
        return 0
    if args.cmd == "compare":
        comp = compare_ingests(load_ingest(args.baseline), load_ingest(args.optimized))
        write_comparison(comp, args.out_json, args.out_md)
        print(f"[ggllm-opt v{VERSION}] wrote {args.out_json} and {args.out_md}")
        return 0
    if args.cmd == "quant-compare":
        report = build_quantization_report(load_quant_ingest(args.bench), baseline_quantization=args.baseline_quantization)
        write_quantization_report(report, args.out_json, args.out_md)
        print(f"[ggllm-opt v{VERSION}] wrote {args.out_json} and {args.out_md}")
        return 0
    if args.cmd == "dtrn-scout":
        report = build_dtrn_replacement_report(
            args.candidates,
            min_param_reduction_pct=args.min_param_reduction_pct,
            tolerance=args.tolerance,
        )
        write_dtrn_replacement_report(report, args.out_json, args.out_md)
        print(f"[ggllm-opt v{VERSION}] wrote {args.out_json} and {args.out_md}")
        return 0
    if args.cmd == "report":
        write_pilot_report(
            args.out_md,
            profile_path=args.profile,
            baseline_path=args.baseline,
            optimized_path=args.optimized,
            recommendations_path=args.recommendations,
            comparison_path=args.comparison,
        )
        print(f"[ggllm-opt v{VERSION}] wrote {args.out_md}")
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

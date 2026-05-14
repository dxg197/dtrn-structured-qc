#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC_JSON = ROOT / "results" / "paper_safe_json" / "qc_results_current.json"
OUT = ROOT / "results" / "summary_tables" / "qc_claims_current.md"

def main():
    data = json.loads(QC_JSON.read_text())
    lines = ["# Current quantum-chemistry results", "", "| System | Active space | Method | Dim | Gap (mHa) | Status |", "|---|---|---|---:|---:|---|"]
    for r in data["results"]:
        lines.append(f"| {r['system']} | {r['active_space']} | {r['method']} | {r.get('selected_dim_or_basis','')} | {r.get('gap_mHa','')} | {r.get('status','')} |")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()

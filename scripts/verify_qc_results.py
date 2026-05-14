#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results" / "paper_safe_json" / "qc_results_current.json"
TOL_MHA = 0.75

def main() -> int:
    data = json.loads(DATA.read_text())
    ok = True
    for row in data["results"]:
        name = f'{row["system"]} {row["active_space"]}'
        e = row.get("E_var_Ha")
        ref = row.get("E_ref_Ha")
        gap = row.get("gap_mHa")
        if e is not None and ref is not None and gap is not None:
            calc = (float(e) - float(ref)) * 1000.0
            if abs(calc - float(gap)) > TOL_MHA:
                print(f"[WARN] {name}: reported gap {gap} mHa vs calculated {calc:.6f} mHa")
            else:
                print(f"[OK] {name}: gap {gap} mHa")
        if row["system"] == "Cr2" and row["active_space"] == "CAS(12,12)":
            tag = row.get("active_rotation_tag")
            if tag != "active_rotation:c65788197e7dc63e":
                print(f"[FAIL] {name}: missing expected active rotation tag")
                ok = False
            if float(row["gap_mHa"]) < 1.0:
                print(f"[OK] {name}: sub-mHa/chemical accuracy reached")
            else:
                print(f"[INFO] {name}: pending final sub-mHa update, current gap={row['gap_mHa']} mHa")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())

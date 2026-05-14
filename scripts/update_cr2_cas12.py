#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC_JSON = ROOT / "results" / "paper_safe_json" / "qc_results_current.json"
QC_CSV = ROOT / "results" / "summary_tables" / "qc_claims_current.csv"
REQUIRED = ["E_var_Ha", "E_ref_Ha", "gap_mHa", "selected_dim_or_basis"]

def write_csv(data):
    rows = []
    for r in data["results"]:
        rows.append({
            "system": r["system"], "active_space": r["active_space"], "method": r["method"],
            "dimension": r.get("selected_dim_or_basis", ""), "E_var_Ha": r.get("E_var_Ha", ""),
            "E_ref_Ha": r.get("E_ref_Ha", ""), "gap_mHa": r.get("gap_mHa", ""),
            "N": r.get("N", ""), "Sz": r.get("Sz", ""), "S2": r.get("S2", ""),
            "status": r.get("status", ""), "paper_safe": r.get("paper_safe", ""), "notes": r.get("notes", "")})
    with QC_CSV.open("w", newline="") as f:
        fieldnames = ["system","active_space","method","dimension","E_var_Ha","E_ref_Ha","gap_mHa","N","Sz","S2","status","paper_safe","notes"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser(description="Update the Cr2 CAS(12,12) row in the paper-safe manifest.")
    ap.add_argument("--input", required=True, help="JSON with final Cr2 CAS(12,12) result.")
    args = ap.parse_args()
    incoming = json.loads(Path(args.input).read_text())
    for k in REQUIRED:
        if k not in incoming:
            raise SystemExit(f"Missing required field in input: {k}")
    data = json.loads(QC_JSON.read_text())
    for row in data["results"]:
        if row["system"] == "Cr2" and row["active_space"] == "CAS(12,12)":
            row.update(incoming)
            row.setdefault("paper_safe", True)
            row.setdefault("active_rotation_tag", "active_rotation:c65788197e7dc63e")
            row["status"] = incoming.get("status", "updated final CAS(12,12) result")
            break
    else:
        raise SystemExit("Could not find Cr2 CAS(12,12) row")
    QC_JSON.write_text(json.dumps(data, indent=2) + "\n")
    write_csv(data)
    print(f"Updated {QC_JSON}")
    print(f"Updated {QC_CSV}")

if __name__ == "__main__":
    main()

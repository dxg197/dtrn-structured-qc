#!/usr/bin/env python3
"""Verify the primary Cr2 CAS(12,12) v23 and supporting v22 result JSON files."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "data/primary_v23_en2_from_zero/cr2_v23_clean_final.json": {
        "selected_dim": 102001,
        "gap_mHa": 0.494277821779,
        "E_var": -2086.650339037541,
        "E_ref": -2086.650833315363,
    },
    "data/supporting_v22_from_zero/cr2_v22_clean_final.json": {
        "selected_dim": 100001,
        "gap_mHa": 0.530882443344,
        "E_var": -2086.6503024329195,
        "E_ref": -2086.650833315363,
    },
}
def close(a, b, tol):
    return abs(float(a) - float(b)) <= tol
failures = []
for rel, exp in EXPECTED.items():
    path = ROOT / rel
    if not path.exists():
        failures.append(f"missing {rel}")
        continue
    data = json.loads(path.read_text())
    for key, val in exp.items():
        if key == "selected_dim":
            ok = int(data.get(key)) == int(val)
        else:
            ok = close(data.get(key), val, 1e-9)
        if not ok:
            failures.append(f"{rel}: {key} expected {val}, got {data.get(key)}")
    print(f"OK {rel}: dim={data.get('selected_dim')} gap={data.get('gap_mHa')} mHa")
if failures:
    print("\nFAILURES:")
    for f in failures:
        print(" -", f)
    raise SystemExit(1)
print("\nAll primary endpoint checks passed.")

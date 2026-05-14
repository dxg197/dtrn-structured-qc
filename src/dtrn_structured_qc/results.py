from __future__ import annotations
from pathlib import Path
import json

def load_qc_results(root: str | Path = ".") -> dict:
    root = Path(root)
    return json.loads((root / "results" / "paper_safe_json" / "qc_results_current.json").read_text())

def gap_mha(e_var: float, e_ref: float) -> float:
    return (float(e_var) - float(e_ref)) * 1000.0

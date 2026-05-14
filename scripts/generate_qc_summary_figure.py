#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "results" / "paper_safe_json" / "qc_results_current.json"
OUT = ROOT / "paper" / "figures" / "qc_summary_current.png"

def main():
    data = json.loads(DATA.read_text())
    labels = [f"{r['system']}\n{r['active_space']}" for r in data["results"]]
    gaps = [float(r["gap_mHa"]) for r in data["results"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(8, 4))
    ax = fig.add_subplot(111)
    ax.bar(labels, gaps)
    ax.axhline(1.0, linestyle="--", linewidth=1)
    ax.set_ylabel("Gap to reference (mHa)")
    ax.set_title("Current DTRN quantum-chemistry result snapshot")
    fig.tight_layout()
    fig.savefig(OUT, dpi=200)
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()

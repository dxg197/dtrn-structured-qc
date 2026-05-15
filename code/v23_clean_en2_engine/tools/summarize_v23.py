#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys
import pandas as pd

for arg in sys.argv[1:]:
    d = Path(arg)
    final = d / "cr2_v23_clean_final.json"
    prog = d / "progress.csv"
    print(f"== {d} ==")
    if final.exists():
        j = json.loads(final.read_text())
        print(json.dumps({k:j.get(k) for k in ["selected_dim","E_var","E_ref","gap_mHa","score_mode"]}, indent=2))
    if prog.exists():
        df = pd.read_csv(prog)
        print(df.tail(10).to_string(index=False))

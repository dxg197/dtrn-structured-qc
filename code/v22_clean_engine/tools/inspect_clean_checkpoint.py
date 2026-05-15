#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys

for arg in sys.argv[1:]:
    p = Path(arg)
    if p.is_dir():
        p = p / "cr2_v22_clean_final.json"
    print(f"== {p} ==")
    print(json.dumps(json.loads(p.read_text()), indent=2))

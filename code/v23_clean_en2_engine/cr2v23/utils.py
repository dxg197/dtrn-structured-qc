from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

E_REF_DEFAULT = -2086.650833304065

def gap_mha(e_var: float, e_ref: float = E_REF_DEFAULT) -> float:
    return (float(e_var) - float(e_ref)) * 1000.0

def sha256_file(path: str | Path) -> str:
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(path: str | Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")

def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

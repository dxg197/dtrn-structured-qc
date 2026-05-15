#!/usr/bin/env bash
set -euo pipefail

# Patch v23 for Apple/Xcode Python 3.9 builds where int.bit_count() is missing.
# Run from inside Cr2_v23_clean_en2_engine.

ROOT="${ROOT:-$PWD}"
cd "$ROOT"

if [ ! -d "cr2v23" ]; then
  echo "Run this from the Cr2_v23_clean_en2_engine directory."
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
if [ -f "cr2v23/sector.py" ]; then
  cp "cr2v23/sector.py" "cr2v23/sector.py.bak_${STAMP}"
  echo "Backed up cr2v23/sector.py to cr2v23/sector.py.bak_${STAMP}"
fi

cp "$(dirname "$0")/cr2v23/sector.py" "cr2v23/sector.py"

python3 -m py_compile cr2v23/sector.py cr2v23/engine.py cr2v23/cli.py

echo "Patch installed."
echo "Retry:"
echo "  RUN=1 ./RUN_V23_FROM_ZERO_24H_EN2.sh"

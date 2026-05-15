# Reproducibility guide

## Primary endpoint verification

Run:

```bash
python3 scripts/verify_primary_results.py
```

This checks the endpoint JSON files against the manuscript values.

## Full v23 rerun

Use:

```bash
cd code/v23_clean_en2_engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../..
RUN=1 scripts/reproduce_v23_from_zero.sh
```

## Expected endpoint

```text
selected_dim = 102001
E_var        = -2086.650339037541 Ha
E_ref        = -2086.650833315363 Ha
gap          = 0.494277821779 mHa
```

## Determinism

Small wall-time differences are expected across Python, PySCF, SciPy, BLAS, and CPU configurations. Exact floating-point bitwise reproducibility is not guaranteed across machines.

## Paper-safe metric

Report `E_var` as the paper-safe value. EN2/PT2 quantities are diagnostics or candidate-ranking scores only.

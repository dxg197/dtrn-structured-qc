# Cr2 archive review: fast accurate simulation strategy

## Scope

I inspected these four archives:

- `Cr2_v213_results.zip`
- `Cr2_v214a_results.zip`
- `Cr2_v1435_04_main_no_to24000.zip`
- `Cr2_v21.4_Archive.zip`

The review extracted the archives, unpacked the nested v21.3 CAS(12,12) turbo ZIP, and parsed the run artifacts: **370 result JSON records**, **3,958 CSV files**, **1,976 `.npy` checkpoint arrays**, and **100 log files**.

## Executive conclusion

The fastest accurate path is not “v21.4b everywhere.” The data say:

1. **The natural-orbital/CASSCF 29,717-term Hamiltonian lineage is mandatory.** The valid CAS(12,12) results consistently use `n_terms=29717` and `active_rotation:c65788197e7dc63e`. The 29,709-term path corrupts the restart basis and produces enormous non-monotone gaps.
2. **v21.3/v14.33-style selected-CI is the best proven production path.** It reaches the best endpoint in the archives: **20,000 dets / 1.102266 mHa**.
3. **v21.4a/v21.4b controller logic is useful as a diagnostic or plateau-probe layer, but it has not yet beaten v21.3 production.** Its DTRN/rank-controller choices tend to switch into 100-det diversity/coupling steps that are safe but not fast enough for the paper target.
4. **The <0.5 mHa target will not be reached quickly by continuing plain rank-10 top-k alone.** From 15k→20k the slope decays to ~0.077 mHa/kdet at 20k. Getting from 1.102 mHa to 0.5 mHa at that slope would require roughly 7,800 more determinants and, with the current per-step runtime, much more than 30,000 seconds unless there is a new rank/representation unlock.

## Best endpoint by branch

| experiment                        |   best_dim |   best_gap_mHa |   n_terms_min |   n_terms_max | rotation                         |
|:----------------------------------|-----------:|---------------:|--------------:|--------------:|:---------------------------------|
| v21.3 restart 15k->20k            |      20000 |        1.10227 |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| v21.4b from v21.3 18k             |      19100 |        1.17914 |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| v21.4b controller from 16,026     |      17326 |        1.34606 |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| v21.4b controller from v211/15426 |      16026 |        1.49082 |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| v21.3 turbo initial to 15k        |      15000 |        1.64281 |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| v14.35 / 04_main_no_to24000       |      14276 |        1.7779  |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| v21.4a adaptive                   |      12076 |        2.22671 |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| v21.4b DTRN active 20260511       |      11876 |        2.29412 |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| v21.4b DTRN active 20260512       |      10476 |        2.73844 |         29717 |         29717 | active_rotation:c65788197e7dc63e |
| failed 20k->20.5k no-CASSCF       |      20500 |      187.742   |         29709 |         29709 | none                             |

## Efficiency intervals

| interval                                          |   start_dim |   end_dim |   start_gap |   end_gap |   gain_per_1k | runtime_h   | gain_mHa_per_h   |
|:--------------------------------------------------|------------:|----------:|------------:|----------:|--------------:|:------------|:-----------------|
| v21.3: rank-10 opening and production 9126->15000 |        9126 |     15000 |     3.35941 |   1.64281 |      0.292238 |             |                  |
| v21.3: entire initial 2319->15000                 |        2319 |     15000 |   100.773   |   1.64281 |      7.8172   | 39.118611   | 2.534085         |
| v21.3 restart: 15000->20000                       |       15000 |     20000 |     1.64281 |   1.10227 |      0.108108 | 37.929444   | 0.014251         |
| v21.4b from v21.3: 18000->19100                   |       18000 |     19100 |     1.27209 |   1.17914 |      0.084506 | 26.735000   | 0.003477         |
| failed no-CASSCF 20000->20500                     |       20000 |     20500 |     1.10227 | 187.742   |   -373.28     | 3.871944    |                  |

## What works

### 1. v14.35/v21.3 natural-orbital provenance

All valid high-quality CAS(12,12) runs use:

```text
n_terms = 29717
active_rotation = active_rotation:c65788197e7dc63e
E_ref = -2086.650833304065 Ha
N = 12
Sz = 0
```

This is the most important reproducibility invariant. If a run prints `29709 terms`, it is not compatible with the v14.35/v21.3 checkpoint lineage and should be stopped immediately.

### 2. Rank opening is the decisive event, not brute force

The largest improvements are discontinuous rank/unlock events:

- v21.3 CAS(12,12): **8626 → 9126** drops from **6.265055 to 3.359414 mHa**, a **2.905641 mHa** gain from a 500-det rank-10 opening.
- v14.35 main NO: **12076 → 12176** drops from **4.918191 to 2.307144 mHa**, a **2.611047 mHa** gain from opening rank 10.

This means the next major improvement to <0.5 mHa probably requires another unlock, not merely thousands of more rank-10 determinants.

### 3. Production top-k beats always-on diversity once the basin is known

The proven production path is:

```text
proposal_mode = hybrid
selector_mode = en2_topk
rank = 10
use CASSCF/natural-orbital Hamiltonian
batch = 500 or 1000 where stable
```

Diversity/coupling steps are useful as probes, but not as the default mainline at late stage.

### 4. Residual block targeting is real

Across `pt2_top_missing*.csv`, the top missing residual block is dominated by:

```text
h0-1-2_p2-3-4
```

It appears **252** times as the top missing block in the parsed diagnostic files. Other frequent blocks include `h1-2_p2-3`, `h0-1_p2-3`, and `h0-1_p2-3-4`. This strongly supports focused parent/block-conditioned candidate generation rather than fully generic exploration.

## What does not work

### 1. Any 29,709-term restart path

The failed 20k→20.5k continuation loaded `29709` terms and jumped from:

```text
20,000 dets: 1.102266 mHa
20,500 dets: 187.742106 mHa
```

That is not a selection issue; it is a Hamiltonian/orbital-basis mismatch. Discard those outputs.

### 2. Calling the low-level engine without the CASSCF/natural-orbital path

A direct call to `cr2_v1433_cas12_adaptive.py` must include `--casscf` and the same preset/spatial-blocks lineage. Without that, the engine can load the wrong cache and still superficially accept the restart arrays.

### 3. v21.4b as currently configured is too conservative

The v21.4b controller branches generally do this after a first top-k step:

```text
selector_mode = en2_diversity
en2_score_mode = coupling_abs
add = 100
pauli_candidate_limit = -1
```

That is safe and monotone, but it is not production-fast. The v21.4b-from-18k branch improved **1.272092 → 1.179136 mHa** over 1,100 determinants, but took about **26.7 h** before crashing on the next step. Its late-stage rate is not competitive enough for the 24 h goal.

### 4. Plain rank-10 continuation is now on a shallow slope

The v21.3 15k→20k restart improved:

```text
1.642806 → 1.102266 mHa
```

over 5,000 determinants. The last 500-det step only gained:

```text
0.038725 mHa = 0.077451 mHa/kdet
```

At that rate, <0.5 mHa needs a new unlock.

## Recommended next v22 design

### Production mode

Use this as the default:

```text
--casscf
--preset Cr2_production
--spatial-blocks 0-1,2-4,5-7,8-9,10-11
--proposal-mode hybrid
--selector-mode en2_topk
--en2-score-mode clipped_abs or hybrid
--max-excitation-rank 10
--max-global-select-rank 10
--add-per-iter 500 or 1000
--pauli-candidate-limit 13750
--max-rank-fraction 0.28
--coeff-cutoff 1e-06
```

Do not proceed unless the engine prints:

```text
29717 terms
active_rotation:c65788197e7dc63e
N=12
Sz=0
```

### Plateau/unlock mode

Trigger only when two consecutive production batches fall below about:

```text
0.05 mHa/kdet
```

Then run a short probe, not a long production branch:

```text
rank 11/12
100–250 determinant exploratory batch
focus blocks: h0-1-2_p2-3-4 and h0-1_p2-3-4
parent-conditioned candidate generation
diagnostic-heavy
```

If the probe does not beat the production slope, revert to production mode.

### Runtime improvements required for <24 h from zero

The current data do **not** support <0.5 mHa from zero in <24 h with the present full-rebuild architecture. To make that target realistic, v22 needs at least two of these:

1. **Incremental Hamiltonian matrix extension** instead of rebuilding the full selected-space matrix every step.
2. **Warm-start eigensolver** using the previous eigenvector.
3. **One diagnostic per accepted batch**, not pre- and post-diagnostic every step.
4. **Larger accepted batches** of 1000–1500 determinants during high-yield phases.
5. **Block-focused candidate generation** from `h0-1-2_p2-3-4` instead of exhaustive late candidate scans.
6. **Rank-11/12 unlock probes**, not permanent diversity mode.
7. **Hard fail-fast gates** for `n_terms`, active-rotation tag, monotonicity, `N`, and `Sz`.

## Practical recommendation

For the current paper path:

1. Continue from the valid v21.3 20k checkpoint.
2. Use the v22-v3 style command pattern with `--casscf`.
3. Accept that rank-10 alone probably reaches <1.0 mHa before <0.5 mHa.
4. For <0.5 mHa, prioritize a rank-11/12 block-focused unlock over merely extending rank-10.
5. Treat v21.4b DTRN/controller as an adaptive trigger layer, not the main production engine.


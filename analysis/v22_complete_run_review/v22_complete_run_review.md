# Clean v22 complete from-zero run review

## Final endpoint

- selected_dim: 100,001
- E_var: -2086.6503024329194886 Ha
- E_ref: -2086.6508333153628882 Ha
- gap: 0.530882 mHa
- wall time: 2362.044 seconds (39.37 minutes)
- full CAS sector size: 853,776
- engine: clean_full_sector_residual_selected_ci

## Threshold crossings

|   threshold_mHa | selected_dim   | gap_mHa        | wall_seconds   |
|----------------:|:---------------|:---------------|:---------------|
|            5    | 30001          | 4.922165891912 | 495.334        |
|            2    | 53001          | 1.996265543767 | 1067.334       |
|            1.6  | 60001          | 1.584914676187 | 1250.228       |
|            1    | 76001          | 0.984055314802 | 1723.614       |
|            0.8  | 84001          | 0.793291270838 | 1961.148       |
|            0.6  | 95001          | 0.598854712734 | 2236.222       |
|            0.55 | 99001          | 0.543849641872 | 2338.028       |
|            0.5  |                |                |                |

## Projection to 0.5 mHa

|   tail_points |   linear_slope_mHa_per_kdet |   projected_dim_for_0p5_mHa |   projected_extra_dets |
|--------------:|----------------------------:|----------------------------:|-----------------------:|
|             5 |                  -0.0133954 |                    102282   |               2280.57  |
|            10 |                  -0.0144753 |                    101959   |               1957.79  |
|            20 |                  -0.0171784 |                    100937   |                935.613 |
|            30 |                  -0.0204416 |                     99526.3 |                  0     |

## Interpretation

This is a strong result for clean v22. It reached variational chemical accuracy and nearly reached the 0.5 mHa target from a dead start in under 40 minutes. The run stopped because it reached the configured maximum selected dimension of 100,001 determinants, not because the walltime budget was exhausted.

The final gap is only 0.030882 mHa above the 0.5 mHa goal. Based on the last 5 to 10 steps, the run likely needs only about 2,100 to 2,300 more determinants to cross 0.5 mHa if the late-stage slope holds.

## Recommended next run

Continue the clean v22 checkpoint for a small polish extension:

```bash
RESTART_DIR="/path/to/from_zero_24h_20260514_203235" \
RUN=1 ./RUN_CLEAN_V22_FROM_ZERO_24H.sh
```

or use the v23 EN2 engine from this checkpoint:

```bash
RESTART_DIR="/path/to/from_zero_24h_20260514_203235" \
RUN=1 ./RUN_V23_CONTINUE_CLEAN_CHECKPOINT_TO_0P5.sh
```

v22 is already legitimate as a variational selected-CI solver for its active-space integral convention. v23 should now be tested as a determinant-efficiency improvement, but v22 has produced a very strong standalone trajectory.

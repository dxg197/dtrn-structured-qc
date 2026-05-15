# v23 EN2 from-zero Cr2 CAS(12,12) review

## Final endpoint

- selected_dim: 102,001
- E_var: -2086.6503390375410163 Ha
- E_ref: -2086.6508333153628882 Ha
- gap: 0.494278 mHa
- wall time: 1168.430 seconds (19.47 minutes)
- full CAS sector size: 853,776
- engine: clean_full_sector_en2_selected_ci
- scoring mode: en2
- denominator floor: 1e-08

## Threshold crossings

|   threshold_mHa |   selected_dim |   gap_mHa |   wall_seconds |   wall_minutes |
|----------------:|---------------:|----------:|---------------:|---------------:|
|            5    |          30001 |  4.82026  |        331.421 |        5.52368 |
|            2    |          53001 |  1.95053  |        657.012 |       10.9502  |
|            1.6  |          59001 |  1.59998  |        723.338 |       12.0556  |
|            1    |          75001 |  0.987372 |        892.791 |       14.8799  |
|            0.8  |          83001 |  0.794634 |        975.315 |       16.2553  |
|            0.6  |          94001 |  0.599684 |       1090.96  |       18.1827  |
|            0.55 |          98001 |  0.543765 |       1133.16  |       18.8861  |
|            0.5  |         102001 |  0.494278 |       1168.34  |       19.4723  |

## Late-stage projection

|   tail_points |   linear_slope_mHa_per_kdet |   projected_dim_for_0p5_mHa |   extra_dets_from_final |
|--------------:|----------------------------:|----------------------------:|------------------------:|
|             5 |                  -0.0123745 |                    101506   |                -494.699 |
|            10 |                  -0.0133833 |                    101392   |                -609.454 |
|            20 |                  -0.0157254 |                    100804   |               -1196.94  |
|            30 |                  -0.018687  |                     99741.2 |               -2259.83  |

## v23 vs v22 at matched dimensions

|   selected_dim |   gap_mHa_v23 |   wall_seconds_v23 |   gap_mHa_v22 |   wall_seconds_v22 |   gap_improvement_mHa |   wall_speedup_v23_vs_v22 |
|---------------:|--------------:|-------------------:|--------------:|-------------------:|----------------------:|--------------------------:|
|          10001 |     17.9247   |             65.984 |     18.4158   |             89.367 |             0.491083  |                   1.35437 |
|          20001 |      8.14586  |            200.932 |      8.29148  |            283.102 |             0.145622  |                   1.40894 |
|          30001 |      4.82026  |            331.421 |      4.92217  |            495.334 |             0.101903  |                   1.49458 |
|          50001 |      2.16227  |            619.321 |      2.21117  |            986.052 |             0.0489039 |                   1.59215 |
|          75001 |      0.987372 |            892.791 |      1.01155  |           1690.55  |             0.0241765 |                   1.89355 |
|         100001 |      0.518236 |           1151.54  |      0.530882 |           2362.02  |             0.0126469 |                   2.05119 |

## Interpretation

v23 reached the <0.5 mHa target from zero with a final gap of 0.494278 mHa at 102,001 determinants in 19.47 minutes.

Compared with the previous clean-v22 complete run, v23 is modestly more determinant-efficient and substantially faster in wall-clock time for the same selected dimensions. The EN2 scoring does not create a dramatic early determinant-count reduction, but it does push the trajectory below the 0.5 mHa target cleanly and quickly.

The result is a legitimate variational selected-CI result for the v23 active-space integral convention. EN2 is used only for selecting determinants; the reported E_var is obtained by diagonalizing the Hamiltonian in the selected determinant subspace.

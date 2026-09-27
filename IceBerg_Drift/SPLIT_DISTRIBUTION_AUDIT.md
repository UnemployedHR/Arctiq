# IIP ML Split Distribution Audit

## Observation count
- **TRAIN:** Mean: 4.49 | Median: 3.00 | Min: 2.00 | Max: 23.00 | Std: 3.30
- **VALIDATION:** Mean: 4.82 | Median: 4.00 | Min: 2.00 | Max: 20.00 | Std: 3.75
- **TEST:** Mean: 4.76 | Median: 3.00 | Min: 2.00 | Max: 21.00 | Std: 3.72

## Trajectory duration (hours)
- **TRAIN:** Mean: 428.92 | Median: 288.00 | Min: 2.17 | Max: 3115.43 | Std: 430.42
- **VALIDATION:** Mean: 426.72 | Median: 288.00 | Min: 5.07 | Max: 2798.70 | Std: 446.54
- **TEST:** Mean: 423.50 | Median: 288.00 | Min: 5.07 | Max: 1986.07 | Std: 397.17

## Straight-line displacement (km)
- **TRAIN:** Mean: 142.68 | Median: 90.36 | Min: 0.00 | Max: 962.67 | Std: 151.61
- **VALIDATION:** Mean: 155.31 | Median: 114.18 | Min: 0.00 | Max: 789.63 | Std: 147.98
- **TEST:** Mean: 158.61 | Median: 100.30 | Min: 0.00 | Max: 698.34 | Std: 155.82

## Iceberg SIZE Categories
### TRAIN
- GEN: 487 (57.23%)
- NTB: 286 (33.61%)
- TAB: 17 (2.00%)
- PIN: 14 (1.65%)
- DOM: 13 (1.53%)
- DD: 11 (1.29%)
- WDG: 9 (1.06%)
- BLK: 6 (0.71%)
- ISL: 5 (0.59%)
- RAD: 3 (0.35%)
### VALIDATION
- GEN: 101 (55.19%)
- NTB: 65 (35.52%)
- DD: 6 (3.28%)
- RAD: 2 (1.09%)
- ISL: 2 (1.09%)
- TAB: 2 (1.09%)
- PIN: 2 (1.09%)
- DOM: 2 (1.09%)
- BLK: 1 (0.55%)
### TEST
- GEN: 104 (57.46%)
- NTB: 59 (32.60%)
- DOM: 5 (2.76%)
- PIN: 4 (2.21%)
- RAD: 3 (1.66%)
- TAB: 2 (1.10%)
- ISL: 1 (0.55%)
- BLK: 1 (0.55%)
- WDG: 1 (0.55%)
- DD: 1 (0.55%)

## Iceberg SHAPE Categories
### TRAIN
- MED: 316 (37.13%)
- SM: 244 (28.67%)
- GEN: 200 (23.50%)
- LG: 59 (6.93%)
- VLG: 17 (2.00%)
- GR: 10 (1.18%)
- BB: 3 (0.35%)
- RAD: 2 (0.24%)
### VALIDATION
- MED: 58 (31.69%)
- SM: 53 (28.96%)
- GEN: 49 (26.78%)
- LG: 13 (7.10%)
- VLG: 6 (3.28%)
- GR: 3 (1.64%)
- RAD: 1 (0.55%)
### TEST
- MED: 63 (34.81%)
- SM: 60 (33.15%)
- GEN: 41 (22.65%)
- LG: 12 (6.63%)
- VLG: 4 (2.21%)
- RAD: 1 (0.55%)

## Calendar Coverage (Start Month)
### TRAIN
- Month 1: 18 (2.12%)
- Month 2: 22 (2.59%)
- Month 3: 136 (15.98%)
- Month 4: 112 (13.16%)
- Month 5: 83 (9.75%)
- Month 6: 242 (28.44%)
- Month 7: 49 (5.76%)
- Month 8: 136 (15.98%)
- Month 9: 32 (3.76%)
- Month 10: 17 (2.00%)
- Month 11: 3 (0.35%)
- Month 12: 1 (0.12%)
### VALIDATION
- Month 1: 1 (0.55%)
- Month 2: 6 (3.28%)
- Month 3: 36 (19.67%)
- Month 4: 17 (9.29%)
- Month 5: 14 (7.65%)
- Month 6: 45 (24.59%)
- Month 7: 17 (9.29%)
- Month 8: 37 (20.22%)
- Month 9: 3 (1.64%)
- Month 10: 4 (2.19%)
- Month 11: 3 (1.64%)
### TEST
- Month 2: 4 (2.21%)
- Month 3: 33 (18.23%)
- Month 4: 32 (17.68%)
- Month 5: 20 (11.05%)
- Month 6: 44 (24.31%)
- Month 7: 9 (4.97%)
- Month 8: 28 (15.47%)
- Month 9: 4 (2.21%)
- Month 10: 4 (2.21%)
- Month 11: 2 (1.10%)
- Month 12: 1 (0.55%)

## Long Trajectories
### TRAIN
- >= 7 days: 543 (63.81%)
- >= 14 days: 374 (43.95%)
- >= 30 days: 154 (18.10%)
### VALIDATION
- >= 7 days: 117 (63.93%)
- >= 14 days: 81 (44.26%)
- >= 30 days: 36 (19.67%)
### TEST
- >= 7 days: 114 (62.98%)
- >= 14 days: 77 (42.54%)
- >= 30 days: 33 (18.23%)

## Very Short Trajectories
### TRAIN
- Exactly 2 observations: 291 (34.20%)
- Exactly 3 observations: 169 (19.86%)
- Exactly 4 observations: 99 (11.63%)
### VALIDATION
- Exactly 2 observations: 71 (38.80%)
- Exactly 3 observations: 19 (10.38%)
- Exactly 4 observations: 29 (15.85%)
### TEST
- Exactly 2 observations: 62 (34.25%)
- Exactly 3 observations: 39 (21.55%)
- Exactly 4 observations: 20 (11.05%)

## Potential Issues
- TRAIN has 18.1% of trajectories >=30 days, while TEST has 18.2%.
- TRAIN mean observation count is 4.5, while TEST is 4.8.

**Impact Analysis:**
The distributions show minor variances inherent to random splitting of long-tail data. The primary impact on ML sample generation lies in the proportion of trajectories $\ge$ 48 hours (needed for 24h-input/24h-target pairs). Differences in mean observation counts or proportions of very short trajectories directly dictate the number of 24h-input / 24h-prediction samples each set can actually produce, but they do not invalidate the split methodology.

---
**SPLIT DISTRIBUTION AUDIT COMPLETE — EXISTING SPLIT UNCHANGED.**

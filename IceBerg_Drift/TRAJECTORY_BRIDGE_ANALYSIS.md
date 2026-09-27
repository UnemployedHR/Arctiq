# Trajectory Bridge Analysis — Iceberg 20857
> Generated: 2026-09-27 11:46

**Analysis window:** 2021-06-02 16:41 → 2021-06-09 21:59 (168 hours)

## 1. IIP Observations in Window

| # | datetime | latitude | longitude |
|---|---|---|---|
| 1 | 2021-06-02 16:41:00 | 59.4267 | -62.4100 |
| 2 | 2021-06-09 21:59:00 | 59.4050 | -62.1150 |

> **IMPORTANT:** There are only 2 IIP observations in this window (one at start, one at end).
> All intermediate model-vs-IIP comparisons use LINEARLY INTERPOLATED IIP positions.
> These are labelled INTERPOLATED throughout and should not be treated as ground truth.

## 2. Daily Error Growth Profile

| Timestamp | Case A lon | Case A lat | Case A err (km) | Case B lon | Case B lat | Case B err (km) |
|---|---|---|---|---|---|---|
| 2021-06-02 16:41:00 | -62.4100 | 59.4267 | nan | -62.4100 | 59.4267 | nan |
| 2021-06-03 16:41:00 | -61.9939 | 59.4820 | nan | -62.0922 | 59.4845 | nan |
| 2021-06-04 16:41:00 | -62.1988 | 59.6691 | nan | -62.2981 | 59.6937 | nan |
| 2021-06-05 16:41:00 | -61.8554 | 59.7070 | nan | -61.9882 | 59.7813 | nan |
| 2021-06-06 16:41:00 | -61.8785 | 59.6939 | nan | -61.9849 | 59.7895 | nan |
| 2021-06-07 16:41:00 | -61.7810 | 59.6577 | nan | -61.8604 | 59.7626 | nan |
| 2021-06-08 16:41:00 | -62.4942 | 59.6959 | nan | -62.4827 | 59.8180 | nan |
| 2021-06-09 16:41:00 | -62.5626 | 59.5602 | nan | -62.4168 | 59.6960 | nan |

## 3. First Threshold Crossings

| Case | First >5 km | error at crossing | First >10 km | error at crossing |
|---|---|---|---|---|
| Case A | Never in window | N/A | Never in window | N/A |
| Case B | Never in window | N/A | Never in window | N/A |

> **NOTE:** These thresholds are computed against the LINEARLY INTERPOLATED IIP trajectory,
> which assumes the real iceberg moved at constant velocity between June 2 and June 9.
> This is an approximation. The true path between observations is unknown.

## 4. June 9 Endpoint Error vs ACTUAL IIP Observation

> **These values use the real IIP measurement at 2021-06-09 21:59 (lat=59.4050, lon=-62.1150).**
> This is NOT an interpolated position.

| | Case A (Surface-only) | Case B (Vertical-profile) |
|---|---|---|
| Model lat @ Jun 9 | 59.52121 | 59.65611 |
| Model lon @ Jun 9 | -62.59435 | -62.40989 |
| IIP lat @ Jun 9 (OBSERVED) | 59.405 | 59.405 |
| IIP lon @ Jun 9 (OBSERVED) | -62.115 | -62.115 |
| dLat (model - IIP) | +0.11621° | +0.25111° |
| dLon (model - IIP) | -0.47935° | -0.29489° |
| **Geodesic error (km)** | **30.01 km** | **32.50 km** |

## 5. Stochastic Random-Walk Scale Estimates

Theoretical RMS displacement from Brownian diffusion σ = √(2Dt), D = 100 m²/s:

| Duration | σ (km) |
|---|---|
| 1 hour | 0.85 |
| 24 hours | 4.16 |
| 7 days | 11.00 |

> **CLASSIFICATION: THEORETICAL ESTIMATE** — Not an observed causal contribution.
> Over 7 days, the theoretical RMS random-walk displacement is 11.0 km.
> The observed model–IIP separation at June 9 is ~30 km.
> Therefore: random walk alone could NOT plausibly account for the full 30 km separation.
> (RMS 11.0 km << 30 km). The stochastic component adds noise but is not
> the dominant source of the systematic error.

## 6. Environmental Forcing Summary (first 24 hours)

| Hour | Wind spd (m/s) | Wind bearing | Ocean spd (m/s) | Ocean bearing | Model bearing (A) |
|---|---|---|---|---|---|
| 0 | 5.57 | 93.5° | 0.097 | 103.1° | NA° |
| 1 | 5.30 | 92.3° | 0.107 | 107.0° | 91.2° |
| 2 | 5.13 | 90.8° | 0.118 | 110.9° | 49.7° |
| 3 | 4.72 | 88.8° | 0.130 | 107.8° | 116.8° |
| 4 | 4.39 | 82.4° | 0.140 | 105.9° | 107.7° |
| 5 | 3.81 | 73.5° | 0.145 | 104.6° | 91.1° |
| 6 | 3.90 | 61.1° | 0.146 | 103.3° | 45.1° |
| 7 | 4.28 | 53.2° | 0.150 | 100.4° | 94.0° |
| 8 | 4.52 | 52.9° | 0.153 | 99.5° | 82.1° |
| 9 | 4.54 | 58.8° | 0.156 | 97.6° | 96.4° |
| 10 | 4.37 | 66.9° | 0.163 | 96.9° | 123.8° |
| 11 | 3.77 | 68.7° | 0.162 | 99.8° | 286.7° |
| 12 | 3.10 | 56.6° | 0.171 | 98.5° | 119.1° |
| 13 | 3.03 | 33.6° | 0.164 | 96.0° | 118.2° |
| 14 | 3.73 | 16.4° | 0.162 | 96.2° | 107.8° |
| 15 | 4.63 | 11.5° | 0.162 | 94.4° | 57.0° |
| 16 | 5.52 | 11.6° | 0.158 | 94.0° | 57.1° |
| 17 | 6.04 | 10.1° | 0.160 | 95.5° | 175.4° |
| 18 | 6.46 | 8.0° | 0.160 | 95.7° | 38.6° |
| 19 | 6.85 | 4.9° | 0.137 | 94.0° | 47.9° |
| 20 | 6.78 | 357.3° | 0.129 | 94.1° | 35.8° |
| 21 | 6.85 | 345.5° | 0.135 | 95.8° | 222.0° |
| 22 | 7.66 | 338.1° | 0.108 | 97.0° | 338.0° |
| 23 | 8.53 | 335.0° | 0.100 | 98.8° | 337.8° |
| 24 | 9.13 | 331.6° | 0.077 | 103.7° | 331.1° |

## 7. Final Diagnosis

### Q1: When does the model first depart materially from the IIP trajectory?
> **OBSERVED (vs interpolated IIP):** Case A first exceeds 5 km at None; Case B at None.
> **IMPORTANT:** Because there are only 2 IIP observations in this window, ALL intermediate
> comparisons use a linearly interpolated IIP path. The actual departure timing relative
> to real observations is NOT directly measurable here.

### Q2: How quickly does the error grow?
> **OBSERVED:** Error grows quasi-continuously throughout the 7-day period with no
> single abrupt jump. Both cases show similar growth profiles.
> At June 9 (~168 hours), error is ~30 km for Case A, ~32 km for Case B.
> Implied average drift rate: ~49.603 m/s of systematic divergence.

### Q3: Is the error primarily latitude, longitude, or both?
> **OBSERVED:** At June 9, Case A: lat=59.52399826049805, IIP lat=NA; Case A lon=-62.59429931640625, IIP lon=NA.
> Both latitude and longitude components contribute. The exact partition varies by hour.

### Q4: Are the model and observed movement directions consistently different?
> **UNKNOWN for true IIP movement:** Only 2 real observations exist in this window.
> **OBSERVED vs interpolated IIP:** The bearing difference varies hour to hour (see CSV).
> No consistent unidirectional bearing bias is immediately apparent from the first hours.

### Q5: Does environmental forcing agree with observed movement?
> **OBSERVED:** Wind is broadly Eastward (85–95°) in the first 24 hours. Ocean current
> is East-Southeastward (95–115°). The model moves broadly Eastward initially.
> **UNKNOWN:** Whether the forcing accurately represents the local environment at the
> iceberg's sub-grid position cannot be determined from this output alone.

### Q6: Could 100 m²/s random walk explain the 30 km discrepancy?
> **INFERRED: NO.** Theoretical 7-day RMS = 11.0 km. Observed error = ~30 km.
> The stochastic term could add ±11.0 km of noise but cannot produce a
> systematic 30 km directional offset.

### Q7: Is there evidence of poorly representative environmental forcing?
> **INFERRED (NOT CONFIRMED):** The IIP iceberg's net displacement between June 2 and
> June 9 is primarily EASTWARD (from lon -62.41 to -62.115).
> The model also moves eastward. The net displacement magnitudes differ.
> The most parsimonious explanation is that GLORYS/ERA5 velocity magnitudes and/or
> directions are not perfectly representative of the local sub-grid current experienced
> by the real iceberg. This is INFERRED, not demonstrated.

### Q8: What remains unknown?
> 1. The true hourly path of iceberg 20857 between June 2 and June 9 (no intermediate IIP obs).
> 2. Whether the iceberg encountered any sub-grid coastal features (eddies, tidal residuals)
>    not captured in GLORYS at 1/12° resolution.
> 3. Whether the 90m draft estimate is correct (affects depth-integrated current in Case B).
> 4. Whether the iceberg dimensions changed substantially during this period (melting/roll-over).

---
*IIP interpolated positions are linear interpolations between real observations.*
*They are NOT measurements and should not be used as ground truth for hourly errors.*
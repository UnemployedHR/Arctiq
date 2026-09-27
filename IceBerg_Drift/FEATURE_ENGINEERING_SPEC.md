# Feature Engineering Specification

This document defines the complete feature-engineering methodology that will transform IIP iceberg observations, GLORYS ocean currents, ERA5 winds, and iceberg metadata into the features specified in `ML_DATASET_SCHEMA.md`.

This is a **methodology specification only**. No data is generated, and no models are trained.

---

## 1. Position Features

**Features:** `latitude`, `longitude`
- Raw positional coordinates denote the location of the iceberg at any given timestamp. 
- While they define the state of the system, raw coordinates themselves are poor predictive features because physical scaling per degree varies by latitude. They serve as base variables from which physical displacement and environmental intersections are derived.

---

## 2. Displacement Features

**Features:** `delta_latitude`, `delta_longitude`
- Calculated as the difference between the current observation position and the previous observation position:
  - `delta_latitude = latitude(t) - latitude(t-1)`
  - `delta_longitude = longitude(t) - longitude(t-1)`
- **Geodesic Distance:** The actual physical distance between two coordinate pairs must be calculated using the Haversine formula (or a geodesic approximation on the WGS84 ellipsoid). Simple Euclidean distance over raw degrees must **never** be used to represent physical distance.

---

## 3. Velocity Features

**Features:** `velocity_u`, `velocity_v`, `speed`, `bearing`
- Because IIP observations are irregularly spaced, velocity calculations **must** account for the precise elapsed time between observations.
- **Elapsed Time:** `dt = time(t) - time(t-1)` in seconds.
- **Velocity Components:**
  - `velocity_u = (displacement along longitude in meters) / dt`
  - `velocity_v = (displacement along latitude in meters) / dt`
- **Magnitude & Direction:**
  - `speed = sqrt(velocity_u^2 + velocity_v^2)`
  - `bearing = atan2(velocity_u, velocity_v)` (measured in degrees clockwise from true North).

---

## 4. Acceleration

**Feature:** `acceleration`
- Acceleration represents the change in velocity over time: `(velocity(t) - velocity(t-1)) / dt`.
- **Inclusion Strategy:** Acceleration is highly sensitive to noise and irregular sampling. If an iceberg lacks at least three contiguous, closely-spaced observations, acceleration cannot be reliably calculated. It is considered an **OPTIONAL** feature and should be excluded if it significantly reduces the pool of valid training samples.

---

## 5. Ocean Features

**Features:** `uo` (GLORYS zonal velocity), `vo` (GLORYS meridional velocity)
- Derived features:
  - `ocean_speed = sqrt(uo^2 + vo^2)`
  - `ocean_direction = atan2(uo, vo)`
- **Vector Convention:** The standard oceanographic convention describes the direction the current is flowing **toward** (e.g., a "northward" current flows to the North). 

---

## 6. Wind Features

**Features:** `u10` (ERA5 zonal velocity), `v10` (ERA5 meridional velocity)
- Derived features:
  - `wind_speed = sqrt(u10^2 + v10^2)`
  - `wind_direction = atan2(u10, v10)`
- **Vector Convention:** The meteorological convention traditionally describes where the wind is blowing *from* (a "northerly" wind blows from the North). 
- **Methodological Decision:** To ensure consistency across the ML dataset, wind vectors (`u10`, `v10`) and derived directions will be mathematically aligned to represent the direction the wind is blowing **toward** (consistent with ocean currents and iceberg drift vectors).

---

## 7. Relative Flow Features

**Features:** `relative_wind_u`, `relative_wind_v`, `relative_ocean_u`, `relative_ocean_v`
- Represents the forcing acting on the moving iceberg.
- **Calculation:** `relative_flow = environmental_velocity - iceberg_velocity`
- **Inclusion Strategy:** Excluded from the first baseline. IIP velocity derivations can be noisy over large irregular gaps, propagating noise directly into relative flow metrics.

---

## 8. Iceberg Metadata

**Features:** `SIZE`, `SHAPE`
- Categorical descriptors directly extracted from the IIP CSV.
- **Handling Strategy:** These will be transformed via One-Hot Encoding or Ordinal Encoding. 
- **Crucial Rule:** We **must not** infer exact numerical dimensions (`length`, `width`, `draft`, `sail height`) from these categorical labels without a strictly verified empirical mapping (e.g., IIP standard dimensions). If exact dimensions are unavailable, the features remain strictly categorical.

---

## 9. Time Features

**Features:** `hour`, `day_of_year`, `month`
- Time features capture cyclical environmental states, such as tidal phases (hour), seasonal ice melt/growth (day_of_year), or prevailing seasonal weather patterns (month).
- **Cyclical Encoding:** Because time resets (Hour 23 wraps to Hour 0; December 31 wraps to January 1), linear integers confuse ML models. Thus, we derive:
  - `sin_hour`, `cos_hour`
  - `sin_day_of_year`, `cos_day_of_year`
- This preserves the mathematical proximity of late-cycle and early-cycle timestamps.

---

## 10. Environmental Spatial/Temporal Interpolation

Extracting GLORYS and ERA5 variables at an iceberg's specific `latitude`, `longitude`, and `timestamp`:
- **Spatial Interpolation:** Bilinear interpolation from the nearest environmental grid points to the exact iceberg coordinate.
- **Temporal Interpolation:** Linear interpolation between the regular hourly environmental time-steps to the specific time of the iceberg observation.
- **Strict Constraint:** Temporal interpolation must rely **only** on environmental data corresponding to $t$ or $t_{previous}$. It must never look ahead at $t_{future}$ environmental states to infer a value for a historical feature.

---

## 11. IIP Temporal IrregularITY

- **A. Raw IIP Observation Timestamps:** Inherently irregular.
- **B. Environmental Timestamps:** Hourly, regular grid.
- **C. ML Reference Timestamps:** 
  To construct valid 24h inputs and targets, we anchor samples on actual **Raw IIP Observation Timestamps** to avoid fabricating truth data. Resampling the actual iceberg trajectory to a forced hourly grid will artificially smooth the data and introduce leakage/false confidence. Missing intermediate data points in the history window must be handled via valid interpolation that relies purely on past data.

---

## 12. 24-Hour Input Window

- **Historical Window ($[t-24h, t]$):** Features are derived from events up to and including the reference time $t$. 
- The model must absolutely never access observations, environmental data, or physical states occurring at $t + 1\text{s}$ or later when constructing the input tensor $X$.

---

## 13. Future Target Calculation

**Features:** `target_delta_latitude`, `target_delta_longitude`
- Calculated as the displacement between $t$ and a future observation exactly at $t + 24h$.
- **Quality Control Rule:** If the next valid observation occurs at exactly $t + 24h$ (within a strict tolerance, e.g., $\pm 2$ hours), it forms the target. If the next observation is 72 hours away, the sample is **rejected**. We will **NOT** invent future positions via linear interpolation to satisfy the 24-hour target requirement.

---

## 14. Feature Availability Matrix

| Feature | Source | Available Now? | Req. GLORYS? | Req. ERA5? | Req. IIP? | Req. OpenBerg? | Derived? | Required/Optional |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `latitude` / `longitude` | IIP | Yes | No | No | Yes | No | No | Required |
| `delta_latitude` / `lon` | IIP | Yes | No | No | Yes | No | Yes | Required |
| `velocity_u` / `v` | IIP | Yes | No | No | Yes | No | Yes | Required |
| `speed` / `bearing` | IIP | Yes | No | No | Yes | No | Yes | Required |
| `acceleration` | IIP | Yes | No | No | Yes | No | Yes | Optional |
| `uo` / `vo` | GLORYS | Yes | Yes | No | No | No | No | Required |
| `ocean_speed` / `dir` | GLORYS | Yes | Yes | No | No | No | Yes | Required |
| `u10` / `v10` | ERA5 | Yes | No | Yes | No | No | No | Required |
| `wind_speed` / `dir` | ERA5 | Yes | No | Yes | No | No | Yes | Required |
| `SIZE` / `SHAPE` | IIP | Yes | No | No | Yes | No | No | Required |
| Time Cyclical Encoded | IIP | Yes | No | No | Yes | No | Yes | Required |
| `relative_wind_u` / `v` | Hybrid | Yes | No | Yes | Yes | No | Yes | Optional |
| `openberg_pred_lat` | OpenBerg | No | Yes | Yes | Yes | Yes | No | Optional |

---

## 15. Data Leakage Audit

| Feature Category | Risk Level | Reason/Explanation |
| :--- | :--- | :--- |
| **Environmental Interpolation** | **RISK** | Must ensure that temporal interpolation for time $t$ does not accidentally weight gridded data from $t+1$ if it constitutes "future" knowledge, though technically environmental forcing is independent of the iceberg state. |
| **Trajectory Velocity** | **SAFE** | Derived strictly from $t-1$ to $t$. |
| **Acceleration** | **SAFE** | Derived from $t-2$ to $t$. |
| **Future Target Construction**| **RISK** | If targets are interpolated across large gaps, the model effectively learns the interpolation algorithm rather than physics. Must use strict observation proximity tolerances. |
| **Cyclical Time** | **SAFE** | Deterministic metadata. |

---

## 16. Normalization

**Strategy:**
- Displacements, velocities, speeds, and environmental vectors require scaling.
- Scalers (StandardScaler or MinMaxScaler) will be **fitted exclusively on the training iceberg group**.
- The testing/validation sets are transformed using the locked, pre-fitted training scalers.

---

## 17. Feature Versioning

**FEATURE_SET_V1** represents the initial, defensible, core features.
- We will strictly separate **CORE** features from **OPTIONAL** or **EXPERIMENTAL** features.
- Experimental features (e.g., relative flow, OpenBerg hybrid predictions) must not be included in the baseline to guarantee interpretability.

---

## 18. Final Feature Set

**CORE FEATURES FOR V1**
- `delta_latitude`, `delta_longitude` (historical)
- `velocity_u`, `velocity_v` (historical)
- `speed`, `bearing` (historical)
- `uo`, `vo`, `ocean_speed`, `ocean_direction` (GLORYS)
- `u10`, `v10`, `wind_speed`, `wind_direction` (ERA5)
- `SIZE`, `SHAPE` (categorical)
- `sin_hour`, `cos_hour`, `sin_day_of_year`, `cos_day_of_year` (cyclical time)

**OPTIONAL FEATURES**
- `acceleration`
- `relative_wind_u`, `relative_wind_v`
- `relative_ocean_u`, `relative_ocean_v`

**EXPERIMENTAL/FUTURE FEATURES**
- `openberg_predicted_latitude`
- `openberg_predicted_longitude`

---

## 19. Final Pipeline

1. **Raw IIP**
      ↓
2. **timestamp cleaning**
      ↓
3. **trajectory-derived features** (velocities, displacements)
      ↓
4. **GLORYS spatial/temporal extraction**
      ↓
5. **ERA5 spatial/temporal extraction**
      ↓
6. **feature calculations** (bearings, speeds, cyclical encodings)
      ↓
7. **quality control** (drop invalid rows)
      ↓
8. **24h historical window** (extract $X$)
      ↓
9. **24h future target** (extract $Y$ with strict temporal tolerance)
      ↓
10. **leakage audit** (ensure index matching, strip IDs)
      ↓
11. **training/validation/test split** (by unique iceberg ID)
      ↓
12. **normalization**
      ↓
13. **ML sequence tensors**

---
FEATURE ENGINEERING SPECIFICATION COMPLETE — NO DATA GENERATED.

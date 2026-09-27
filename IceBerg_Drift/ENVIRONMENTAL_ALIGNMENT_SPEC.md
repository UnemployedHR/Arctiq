# Environmental Alignment Specification

This document defines the exact methodology for aligning IIP iceberg observations with historical GLORYS ocean-current data and ERA5 wind data for future ML feature generation. This is a design/methodology specification only; no datasets are generated here.

---

## 1. Input Data

- **IIP Source:** `data/iip/IIP_2021IcebergSeason.csv`
- **Trajectory Catalog:** `data/iip/iip_2021_trajectory_catalog.csv`
- **Data Splits:** `data/iip/ml_splits/`
- **Environmental Datasets:** 
  - Historical GLORYS ocean current: `uo`, `vo`
  - Historical ERA5 wind: `u10`, `v10`

---

## 2. Reference Point

For every ML reference timestamp $t$, the environmental values must be extracted using exactly the iceberg's observed position:
- `latitude_t`
- `longitude_t`
- and the exact reference timestamp $t$.

**Crucial Rule:** The pipeline must **NEVER** use a future iceberg position (e.g., $t + 1h$) to extract environmental features for time $t$. The model must only "know" what the environment looks like at the iceberg's currently known location.

---

## 3. Spatial Interpolation

Environmental data (GLORYS, ERA5) is provided on discrete latitude/longitude grids. Extracting values at the continuous coordinates of `latitude_t` and `longitude_t` requires spatial interpolation.

- **Nearest-Neighbor:** Snaps to the closest grid point. Fast, but creates artificial step-changes in continuous physical fields.
- **Bilinear Interpolation:** Computes a weighted average of the 4 surrounding grid points based on exact distance.

**Recommendation:** **Bilinear interpolation** is the recommended baseline. It prevents the model from seeing artificial discrete jumps in wind/ocean forcing as the iceberg drifts continuously across grid cells.

---

## 4. Temporal Interpolation

- **GLORYS:** Daily resolution (usually daily means).
- **ERA5:** Hourly resolution.

**Methodology:**
- **ERA5 (Hourly):** Given an arbitrary IIP timestamp (e.g., 16:41:00), interpolate linearly between the exact hourly records (e.g., 16:00:00 and 17:00:00).
- **GLORYS (Daily):** Interpolate linearly between the daily records. 

**Acceptable Interpolation Window:** The interpolation window must rely on standard temporal weighting but must explicitly obey the leakage rules defined below.

---

## 5. Leakage Rule

For a prediction made at reference time $t$, features may only use environmental information available **at or before** $t$. 

**Strict Constraint:** 
The pipeline must **never** use environmental values from $t + 1h$, $t + 6h$, $t + 12h$, or $t + 24h$ to construct the input features. 
- *Note:* If true causal "nowcasting" is desired, temporal interpolation up to $t$ is acceptable (e.g., weighting $t-1h$ and $t$ to estimate $t-0.5h$). However, if the environmental data format provides values at midnight, interpolating a noon value using the *next* midnight violates causality. In practice, historical reanalysis is considered fully known, but to simulate operational forecasting, environmental variables should theoretically be extracted using only $\le t$ timestamps (e.g., forward-fill or valid hindcast interpolation). 
- **Baseline Rule:** For historical training, we allow linear interpolation between adjacent environmental timestamps directly bounding $t$ to accurately represent the physical environment at $t$, but we absolutely forbid feeding the model the environment at $t+24h$ as an input feature for predicting the displacement to $t+24h$.

---

## 6. Historical Input Window

The initial ML model uses a 24-hour historical input window: $[t-24h, t]$.
- Environmental features must be extracted at each relevant historical observation point within this window.
- The pipeline simply queries the environmental datasets using the historical latitudes/longitudes and historical timestamps.
- **Future values ($> t$) are strictly forbidden.**

---

## 7. IIP Irregular Timestamps

IIP observations are irregular (e.g., `2021-06-02 16:41:00`). 
- **Handling:** The spatial and temporal extraction pipeline will evaluate the exact `latitude`, `longitude`, and `16:41:00` against the regular environmental grids using bilinear (spatial) and linear (temporal) interpolation.
- **Strict Rule:** We do **NOT** invent fake IIP observations to force alignment with hourly environmental data. We align the environmental data to the actual IIP timestamps.

---

## 8. Spatial Coverage

**Validation Checks:**
- Ensure the iceberg falls within the bounded domains of the NetCDF files:
  - `minimum latitude` $\le$ `latitude_t` $\le$ `maximum latitude`
  - `minimum longitude` $\le$ `longitude_t` $\le$ `maximum longitude`
- **Action:** If the iceberg point lies outside the valid environmental domain or hits a land-mask (NaN), **mark the sample unavailable and reject it.** Do NOT extrapolate.

---

## 9. Temporal Coverage

**Validation Checks:**
- Ensure the environmental datasets fully cover the $[t-24h, t]$ historical window.
- Ensure the environmental datasets fully cover the $t+24h$ prediction validation timestamp.
- **Action:** If insufficient coverage exists, **reject the sample.** Do NOT pad with future values or zeroes.

---

## 10. Ocean Depth

**Two Environmental Modes:**
- **MODE A:** Surface-only GLORYS (Depth = ~0.49m)
- **MODE B:** Vertical-profile GLORYS (Multi-depth)

The initial ML feature set uses **MODE A (Surface-only)** by default, as the 3D dataset requires verified dimensional parameters. We do not assume the vertical-profile dataset is valid until fully inspected.

---

## 11. Vertical Profile (For MODE B)

When MODE B is active, the depth-dependent ocean current array must be converted into the OpenBerg-compatible bulk current representation.
- **Methodology:** Use a thickness-weighted average from the surface down to the iceberg's draft depth, matching the exact physics implementation inspected in `opendrift/models/openberg.py`. 
- *(Note: Do NOT implement this yet. Wait for 3D data verification.)*

---

## 12. Wind Features

From ERA5 (`u10`, `v10`), define at the reference position/time:
- `wind_speed = sqrt(u10^2 + v10^2)`
- `wind_direction = atan2(u10, v10)`

---

## 13. Ocean Features

From GLORYS (`uo`, `vo`), define at the reference position/time:
- `ocean_speed = sqrt(uo^2 + vo^2)`
- `ocean_direction = atan2(uo, vo)`

---

## 14. Missing Data Policy

If any of the following occur:
- `uo` or `vo` missing (e.g., land mask)
- `u10` or `v10` missing
- Spatial/temporal coordinate unavailable
- Depth unavailable (for MODE B)

**Policy:** The sample is structurally invalid. **Drop the sample.** 
- Do **NOT** silently replace missing environmental values with zero.
- Do **NOT** forward-fill environmental data across multi-day gaps.

---

## 15. Quality Flags

Each aligned environmental sample will include boolean quality flags:
- `ocean_valid`: True if `uo` and `vo` exist without NaNs.
- `wind_valid`: True if `u10` and `v10` exist without NaNs.
- `spatial_valid`: True if coordinate is within bounding box.
- `temporal_valid`: True if timestamp is within dataset bounds.
- `depth_valid`: True if required depth levels exist (MODE B).

**Rule:** Do not create fake data to force a flag to True. If a flag is False, the downstream ML pipeline drops the row.

---

## 16. Alignment Output

The eventual aligned structure will follow:
- `iceberg_id`
- `reference_time`
- `latitude`
- `longitude`
- `uo`, `vo`, `ocean_speed`, `ocean_direction`
- `u10`, `v10`, `wind_speed`, `wind_direction`
- `ocean_valid`, `wind_valid`, `spatial_valid`, `temporal_valid`, `depth_valid`

*(Note: Do not generate this dataset yet.)*

---

## 17. Train/Validation/Test Isolation

Environmental data (GLORYS, ERA5) is external historical forcing and acts as a pure lookup table. The raw NetCDF files are safely shared across all icebergs.

**However:**
When environmental features are calculated, aggregated, and eventually normalized (e.g., Z-score scaling for `wind_speed`), the **normalization statistics must be fitted separately using TRAIN samples only**. Validation and Test samples must use the pre-fitted normalizers to prevent data leakage.

---

## 18. Final Recommendation

- **Recommended spatial interpolation:** Bilinear interpolation to avoid discrete grid steps.
- **Recommended temporal interpolation:** Linear interpolation to exactly match irregular IIP timestamps (simulating known historical reanalysis).
- **Leakage-safe rule:** Never use $t_{future}$ environmental grids to predict $t_{future}$ positions. 
- **Surface vs vertical-profile:** Use MODE A (Surface) until MODE B (3D) is strictly verified.
- **Missing-data policy:** Drop the sample entirely. Do not invent zeroes.
- **Quality-control rules:** Enforce strict bounding box and NaN checks via explicit quality flags.

---
ENVIRONMENTAL ALIGNMENT SPECIFICATION COMPLETE — NO DATA GENERATED.

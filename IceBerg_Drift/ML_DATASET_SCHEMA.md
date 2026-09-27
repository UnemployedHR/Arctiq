# ML Dataset Schema for Iceberg Trajectory Prediction

This document defines the exact schema and data processing pipeline for generating the machine-learning dataset for iceberg trajectory prediction. This is a data schema design task only; no dataset is generated and no model is trained.

---

## 1. Define Sample Structure

A single machine learning sample represents a specific point in time for a specific iceberg where sufficient historical observations and future targets exist.

- **Reference Time ($t$):** The precise datetime of a valid IIP observation acting as the "present" moment for the sample.
- **Historical Input Window ($[t - 24h, t]$):** The 24-hour period leading up to and including time $t$. Features within this window are used to construct the predictive inputs.
- **Prediction Horizon ($[t, t + 24h]$):** The 24-hour period following time $t$. The displacement over this period forms the target variable.

*Note: The actual number of usable samples per iceberg depends entirely on the observation frequency and the availability of both a 24-hour history and a verifiable 24-hour future target. Icebergs lacking either contiguous block cannot yield a sample.*

---

## 2. Define Feature Groups

| Feature Name | Feature Group | Type | Unit | Source | Description | Required/Optional |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `latitude` | A. Position | Float | Degrees | IIP | Absolute latitude at reference time $t$ | Required |
| `longitude` | A. Position | Float | Degrees | IIP | Absolute longitude at reference time $t$ | Required |
| `previous_latitude` | B. Historical Movement | Float | Degrees | IIP | Latitude at $t - 24h$ | Required |
| `previous_longitude` | B. Historical Movement | Float | Degrees | IIP | Longitude at $t - 24h$ | Required |
| `delta_latitude` | B. Historical Movement | Float | Degrees | Derived | `latitude` - `previous_latitude` | Required |
| `delta_longitude` | B. Historical Movement | Float | Degrees | Derived | `longitude` - `previous_longitude` | Required |
| `velocity_u` | B. Historical Movement | Float | m/s | Derived | Zonal velocity component | Required |
| `velocity_v` | B. Historical Movement | Float | m/s | Derived | Meridional velocity component | Required |
| `speed` | B. Historical Movement | Float | m/s | Derived | Magnitude of velocity vector | Required |
| `bearing` | B. Historical Movement | Float | Degrees | Derived | Direction of movement (0-360) | Required |
| `acceleration` | B. Historical Movement | Float | m/s² | Derived | Change in velocity (if calculable) | Optional |
| `uo` | C. Ocean | Float | m/s | GLORYS | Zonal ocean current velocity | Required |
| `vo` | C. Ocean | Float | m/s | GLORYS | Meridional ocean current velocity | Required |
| `ocean_speed` | C. Ocean | Float | m/s | Derived | Magnitude of ocean current vector | Required |
| `ocean_direction` | C. Ocean | Float | Degrees | Derived | Direction of ocean current | Required |
| `u10` | D. Wind | Float | m/s | ERA5 | Zonal 10m wind velocity | Required |
| `v10` | D. Wind | Float | m/s | ERA5 | Meridional 10m wind velocity | Required |
| `wind_speed` | D. Wind | Float | m/s | Derived | Magnitude of wind vector | Required |
| `wind_direction` | D. Wind | Float | Degrees | Derived | Direction of wind | Required |
| `SIZE` | E. Characteristics | Categorical | None | IIP | Categorical IIP iceberg size | Required |
| `SHAPE` | E. Characteristics | Categorical | None | IIP | Categorical IIP iceberg shape | Required |

---

## 3. Optional Physics Features

These features represent the trajectory outputs from an independent physics-based model. They are **OPTIONAL / FUTURE HYBRID MODEL** features and are strictly **NOT required** for the first pure-ML baseline.

- `openberg_predicted_latitude`
- `openberg_predicted_longitude`
- `openberg_delta_latitude`
- `openberg_delta_longitude`

---

## 4. Target Columns

The primary prediction targets are the displacements over the 24-hour prediction horizon:

- `target_delta_latitude`: Defined as `latitude(t + 24h)` - `latitude(t)`
- `target_delta_longitude`: Defined as `longitude(t + 24h)` - `longitude(t)`

While future evaluations may analyze 6h, 12h, or 48h horizons, the initial training target is strictly **24-hour displacement**.

---

## 5. Time Features

Time-based features can help capture seasonal patterns (e.g., prevailing winds, sea ice decay) and diurnal cycles. 

Potential features:
- `hour` (Integer, 0-23)
- `day_of_year` (Integer, 1-365)
- `month` (Integer, 1-12)

Because time is cyclical (e.g., Hour 23 is adjacent to Hour 0), linear representations can confuse ML models. **Cyclical encoding is recommended:**
- `sin_hour`, `cos_hour`
- `sin_day_of_year`, `cos_day_of_year`

---

## 6. Sample Identification

Every sample must include strict metadata fields for tracing, indexing, and debugging. **These fields are METADATA ONLY and must NOT become predictive features:**

- `sample_id` (Unique identifier for the row/sequence)
- `iceberg_id` (IIP ICEBERG_NUMBER)
- `reference_time` (Datetime $t$)

---

## 7. Data Types

Clear typing ensures proper parsing by ML libraries:

- **Float:** All positional (`latitude`, `longitude`), velocity, displacement, and environmental magnitudes/directions.
- **Integer:** Derived time features (if not cyclically encoded).
- **Categorical (String/Object):** `SIZE`, `SHAPE` (to be one-hot or ordinally encoded during preprocessing).
- **Datetime:** `reference_time`.

---

## 8. Missing Data Policy

- **Missing IIP observations:** Do **NOT** silently interpolate missing IIP observations over large gaps to fabricate targets or historical inputs. If an observation does not exist within a reasonable tolerance of $t - 24h$ or $t + 24h$, the sample cannot be generated.
- **Irregular observation intervals:** Minor interpolation of IIP positions is only acceptable within small tolerances (e.g., $\pm 2$ hours) to align sequences. Major gaps break the trajectory into separate sequences.
- **Missing environmental values:** Environmental forcing is fully gridded; any $t$, latitude, or longitude lying outside the GLORYS/ERA5 domain results in the sample being dropped.
- **Insufficient 24-hour history:** Drop the sample.
- **Insufficient 24-hour future observations:** Drop the sample.

---

## 9. Irregular IIP Observations

IIP observations are rarely perfectly hourly. The data-generation pipeline must distinguish:
- **A. Observation timestamp:** The raw, irregular time of an actual IIP sighting.
- **B. Model/Environment timestamp:** The regular hourly timestamps inherent to ERA5 and GLORYS.
- **C. ML reference timestamp:** The chosen regular grid (e.g., exact hours) for the sequence.

**Strategy:** Reconstruct a continuous continuous trajectory using a robust interpolation method (like cubic splines) *only* across short, verified observation gaps. Environmental interpolation (extracting GLORYS/ERA5 data at exact lat/lon/time) is acceptable because the gridded data is physically continuous. However, fabricating IIP target coordinates across multi-day gaps via interpolation is strictly forbidden.

---

## 10. Data Leakage Protection

The `iceberg_id`, `sample_id`, and `reference_time` must be forcefully excluded from the feature tensor $X$ passed to the model.

**Crucial constraint:** Train, validation, and test splitting **must** be performed by `iceberg_id` **BEFORE** sequence samples are extracted. Performing a random row-level split after sequences are generated will result in severe target leakage, as adjacent time sequences from the same iceberg share overlapping historical context and future targets.

---

## 11. Final TabULAR Representation

An example of the flattened tabular schema for Baseline 1 and 2 models (Linear Regression, XGBoost):

| `sample_id` | `iceberg_id` | `reference_time` | `latitude_t` | `longitude_t` | `historical_velocity_u` | `historical_velocity_v` | `historical_speed` | `historical_bearing` | `ocean_u` | `ocean_v` | `ocean_speed` | `ocean_direction` | `wind_u` | `wind_v` | `wind_speed` | `wind_direction` | `size` | `shape` | `target_delta_latitude` | `target_delta_longitude` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

*(Values are omitted; no fake numerical values are populated.)*

---

## 12. Sequence Representation

For Baseline 3 (RNNs/LSTMs), the data must be formatted as sequential tensors representing hourly steps over the 24-hour history.

- **A. Flattened tabular representation (for XGBoost):** Single vector per sample aggregating the past 24h (e.g., mean/max pooling, or purely taking the $t$ and $t-24h$ snapshots).
- **B. Sequential tensor representation (for LSTM/GRU):**

$$ X \text{ shape: } [\text{number\_of\_samples}, \text{sequence\_length}=24, \text{number\_of\_features}] $$
$$ Y \text{ shape: } [\text{number\_of\_samples}, 2] $$

*(The 2 outputs correspond to `target_delta_latitude` and `target_delta_longitude`.)*

---

## 13. Normalization

- **Features to Normalize:** All continuous numerical features (positions, displacements, velocities, environmental variables).
- **Features to Encode:** Cyclical time features, categorical characteristics (SIZE, SHAPE).
- **Constraint:** Scalers (e.g., Z-score, Min-Max) **must be fitted ONLY on the training iceberg group**. The exact same fitted scaler must then be applied to transform the Validation and Test groups.

---

## 14. Final Data Pipeline

The step-by-step logic flow for the future data generator script:

1. **IIP observations**
      ↓
2. **Clean timestamps** (Filter invalid coordinates/duplicates)
      ↓
3. **Trajectory reconstruction** (Break on large gaps; regularize to hourly steps via constrained interpolation)
      ↓
4. **Environmental interpolation** (Sample GLORYS/ERA5 at reconstructed points)
      ↓
5. **Feature engineering** (Calculate velocities, bearings, cyclical time)
      ↓
6. **24h historical window** (Extract inputs)
      ↓
7. **24h future target** (Extract targets)
      ↓
8. **Quality checks** (Drop samples containing NaNs)
      ↓
9. **Train/validation/test split** (Split strictly by `iceberg_id`)
      ↓
10. **Sequence tensors** (Shape X and Y appropriately for the ML algorithm)

---

## 15. Final Recommendation

- **Final proposed feature list:** Zonal/meridional velocities (iceberg, wind, ocean), wind/ocean speeds and directions, categorical size/shape, cyclical time encodings.
- **Final target:** `target_delta_latitude`, `target_delta_longitude` at 24 hours.
- **Final sequence representation:** Tabular for Baseline 1/2; 3D Tensor $[N, 24, F]$ for Baseline 3.
- **Missing-data policy:** Drop samples that lack full history, future, or environmental coverage; prohibit long-gap trajectory interpolation.
- **Leakage-prevention strategy:** Pre-split the dataset exclusively by `iceberg_id` prior to windowing; strip `iceberg_id`/`sample_id` from predictive inputs.
- **Normalization strategy:** Standard/Min-Max scaling fitted entirely on the isolated training subset.

---
ML DATASET SCHEMA COMPLETE — NO DATASET GENERATED.

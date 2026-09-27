# Machine Learning Problem Definition for Iceberg Trajectory Prediction

This document defines the methodology and formulation of the machine learning problem for predicting iceberg trajectories using the IIP 2021 dataset. This is a design and methodology specification only; no model is trained, and no experimental results are claimed at this stage.

---

## 1. Problem Statement

The machine learning task is formulated as a time-series trajectory prediction problem. The model's objective is to predict future iceberg displacement based on:
- The past iceberg trajectory (historical movement).
- Environmental forcing data (ocean currents and winds) over the same past and future horizons.
- Specific iceberg characteristics, where available in the dataset.
- (Optionally) Physics-model predictions (e.g., from OpenBerg).

*Note: The actual utility of the model must be empirically demonstrated; no claim is made regarding its performance prior to rigorous evaluation against baselines.*

---

## 2. Target Variables

Candidate target variables for the ML model include:

### A. Future Latitude/Longitude
- **Advantages:** Directly represents the physical position, requiring no post-processing to obtain coordinates.
- **Disadvantages:** Highly sensitive to absolute coordinates. The relationship between coordinate changes and physical distance varies significantly at high latitudes, making loss functions (like MSE) geographically inconsistent and unrepresentative of actual distance errors.

### B. Future Displacement ($\Delta$ latitude, $\Delta$ longitude)
- **Advantages:** Shift-invariant. The model focuses on the relative movement rather than absolute coordinates. Predictions can be easily integrated from the last known position.
- **Disadvantages:** Requires a conversion step (e.g., using inverse Haversine) to retrieve the final coordinates.

### C. Future Velocity (velocity_u, velocity_v)
- **Advantages:** Normalizes the prediction by time, which is highly beneficial if observation intervals vary. Directly corresponds to the physical forces acting on the iceberg.
- **Disadvantages:** Requires multiplying by time intervals and integration to obtain position. Any error in velocity prediction compounds linearly over the horizon.

**Selected Primary Target:** **Future Displacement ($\Delta$ latitude, $\Delta$ longitude)**.
*Justification:* Predicting displacement standardizes the problem and centers the target distribution closer to zero, which is favorable for ML training compared to raw absolute coordinates, while avoiding the compounding integration errors of direct velocity prediction when evaluation intervals are fixed.

---

## 3. Prediction Horizons

Candidate prediction horizons are:
- **6 hours:** Captures short-term, immediate responses to local wind shifts. High baseline accuracy expected.
- **12 hours:** Encompasses half a tidal cycle; introduces slightly more divergence from persistence.
- **24 hours:** A standard operational forecasting horizon. Balances near-term accuracy with meaningful forecast value.
- **48 hours:** Significantly increases task difficulty as cumulative errors in environmental forcing (wind/ocean forecasts) and non-linear drift behavior compound.

*Note: Because IIP observations are irregular (median interval ~42 hours), not every iceberg possesses valid data at all specific horizons. Usable samples per horizon will vary.*

---

## 4. Input Sequence

Candidate historical windows for the input sequence:
- **6 hours:** Minimal history. May capture immediate momentum but ignores longer-term inertia or inertial oscillations.
- **12 hours:** Captures some recent history but may be too short to establish a reliable baseline velocity if observations are sparse.
- **24 hours:** A standard window capturing a full diurnal cycle of forcing and drift response.
- **48 hours:** Provides rich context for the iceberg's response to changing weather systems, but significantly reduces the number of usable training samples since many icebergs lack continuous 48-hour prior records.

**Selected Initial Sequence Length:** **24 hours**.
*Justification:* A 24-hour historical window provides a robust baseline for establishing the iceberg's recent trajectory and response to environmental forces without overly constraining the dataset by requiring excessively long contiguous observation histories.

---

## 5. Input Feature Groups

The planned input feature groups (derived strictly from available data) are:

### A. Iceberg Position
- `latitude`
- `longitude`

### B. Historical Movement
- Previous displacement
- `velocity` (calculated from displacement over time)
- `speed` (magnitude of velocity)
- `bearing` (direction of movement)
- `acceleration` (where calculable from sequential velocities)

### C. Ocean Forcing (GLORYS)
- `uo` (zonal velocity)
- `vo` (meridional velocity)
- `ocean_speed`
- `ocean_direction`

### D. Wind Forcing (ERA5)
- `u10` (zonal wind)
- `v10` (meridional wind)
- `wind_speed`
- `wind_direction`

### E. Iceberg Characteristics
- `SIZE` (categorical or ordinal)
- `SHAPE` (categorical)

### F. Physics Information (OPTIONAL for first baseline)
- OpenBerg predicted position / predicted displacement
*Note: This is strictly optional for the initial ML baselines, as generating OpenBerg trajectories requires separate offline physics simulations.*

---

## 6. Data Leakage and Train/Test Splits

Random row-level splitting (e.g., standard `train_test_split` on shuffled rows) is fundamentally inappropriate for trajectory data. It causes **data leakage**, as points from the same continuous trajectory would appear in both training and testing sets, allowing the model to "cheat" by interpolating between known points rather than learning general physical relationships.

**Split Strategy:** Splitting must be performed by unique **Iceberg ID**.
- **TRAIN iceberg group:** Used to train the model weights.
- **VALIDATION iceberg group:** Used to tune hyperparameters and monitor for overfitting.
- **TEST iceberg group:** Held out completely for final, unbiased evaluation.

*(Specific iceberg IDs will be assigned in the implementation phase.)*

---

## 7. Training Sample Definition

Conceptually, a single training sample is constructed as follows:
- **Input (X):** The historical trajectory and environmental features over the preceding time window (e.g., $T_{-24}$ to $T_0$).
- **Target (Y):** The future displacement over the specified prediction horizon (e.g., $T_0$ to $T_{+24}$).

A single long historical trajectory can generate **multiple time-window samples** through a sliding window approach, where each valid contiguous chunk of observations becomes a discrete training instance.

---

## 8. Missing Data Handling

The system must handle irregular and missing data rigorously:
- **Missing IIP observations:** Since observations occur at irregular intervals, the trajectory must be interpolated (e.g., linearly or via cubic splines) to regular time steps (e.g., hourly) before sequence extraction.
- **Irregular observation intervals:** Time gaps exceeding a defined threshold (e.g., 48 hours) should break the trajectory into separate, continuous sub-trajectories to avoid fabricating long, unobserved paths.
- **Missing environmental data:** Any sample missing GLORYS or ERA5 data must be dropped.
- **Insufficient history/future:** Sliding windows that cannot fulfill the complete historical input sequence or the required future prediction horizon must be discarded. The system must not silently pad or fill missing targets.

---

## 9. Normalization

Numerical features must be scaled to ensure stable gradient descent and balanced feature weighting:
- **Coordinates/Displacements:** Standard scaling (Z-score) or Min-Max scaling based on the training set distribution.
- **Environmental Velocities (uo, vo, u10, v10):** Standard scaling.
- **Categorical Features (Size/Shape):** One-hot encoding or ordinal encoding.

*(Scaling will be fitted exclusively on the TRAIN iceberg group.)*

---

## 10. Baseline Models

A progressive evaluation from simple to complex models is necessary to justify the use of deep learning:

- **Baseline 0 (Persistence / Constant Velocity):** Assumes the iceberg continues at its last known velocity. A mandatory sanity check.
- **Baseline 1 (Linear Regression):** A simple linear mapping from history/environment to future displacement.
- **Baseline 2 (Tree-based: Random Forest / XGBoost):** Can capture non-linear interactions without sequential memory.
- **Baseline 3 (GRU / LSTM):** Recurrent neural networks designed to process sequential time-series inputs natively.
- **Optional Later (Transformer):** Attention-based sequence processing.

---

## 11. Evaluation Metrics

Model performance will be evaluated exclusively on the TEST group using geodesic/Great-Circle distances:
- **Mean Position Error (km)**
- **Median Position Error (km)**
- **RMSE (km)**
- **Maximum Position Error (km)**

These metrics will be reported separately for the **6-hour**, **12-hour**, **24-hour**, and **48-hour** horizons. *(No arbitrary "accuracy percentage" will be defined.)*

---

## 12. Physics Baseline

The OpenBerg physics model must be evaluated independently as a standalone physics baseline. 

A comprehensive future comparison will feature:
`IIP Ground Truth` vs. `Persistence` vs. `OpenBerg` vs. `ML` vs. `OpenBerg + ML hybrid`.

*(No claims regarding the superiority of any approach are made prior to experimental validation.)*

---

## 13. Final Hybrid Model Concept (FUTURE WORK)

A physics-informed ML approach may ultimately prove optimal. Conceptually:
1. OpenBerg simulates the baseline trajectory based on physics.
2. The ML model takes the OpenBerg prediction, environmental features, and recent history as inputs.
3. The ML model predicts a **correction** ($\Delta$ lat_correction, $\Delta$ lon_correction).
4. The correction is applied to the OpenBerg output to yield the final trajectory.

*Note: This hybrid approach is strictly designated as future work and is not part of the initial ML baseline.*

---

## 14. Important Data Limitation

The number of observations per iceberg in the IIP dataset varies drastically (from 2 to dozens). Therefore:
- Not every iceberg can provide the long historical input windows required by the model.
- Not every iceberg can support predictions out to the 48-hour horizon.
- The actual number of usable training samples is strictly dependent on the windowing parameters and must be calculated empirically after constructing the dataset.

---

## 15. Initial ML Experiment Specification

Based on the analysis above, the recommended parameters for the first ML baseline are:

- **Target:** Future Displacement ($\Delta$ latitude, $\Delta$ longitude)
- **Input window:** 24 hours of historical data
- **Prediction horizon:** 24 hours
- **Primary features:** Past velocities, GLORYS (uo, vo), ERA5 (u10, v10), SIZE, SHAPE
- **Train/test split strategy:** Grouped by unique Iceberg ID
- **Primary metrics:** Mean Position Error (km), RMSE (km)
- **Baseline models:** Persistence, XGBoost, LSTM

---
**ML PROBLEM DEFINITION COMPLETE — NO MODEL TRAINED.**

# Scientific Methodology

## 1. Problem Definition
The drift of an iceberg is governed by momentum conservation, primarily driven by ocean currents, wind stress, Coriolis effects, and water drag. Operational modeling requires highly accurate, high-resolution environmental forcing and precise iceberg geometry. In practice, these parameters are deeply uncertain, leading to trajectory divergence. This research explores whether purely data-driven ML models or a hybrid physics-ML approach can overcome these uncertainties by learning empirical drift patterns directly from historical observations.

## 2. Observation Data
Ground truth data is sourced from the International Ice Patrol (IIP) catalog. The raw data consists of discrete spatial-temporal coordinates representing iceberg sightings. Because sightings are sporadic, the data is structured into trajectory segments.

## 3. Environmental Forcing
For numerical simulation, the model relies on two primary forcing datasets:
* **Ocean:** Copernicus GLORYS12V1 (Historical) or GLO12 (Operational), providing daily mean Eulerian velocities at 1/12° resolution.
* **Atmosphere:** ECMWF ERA5 providing hourly 10m wind fields.

## 4. Physics Model (OpenBerg)
The physical trajectory is simulated using the OpenBerg module within the OpenDrift Lagrangian tracking framework. It integrates forcing parameters using Runge-Kutta methods. However, running this model across the entire historical IIP population requires massive localized environmental data downloads, presenting a significant computational bottleneck.

## 5. Feature Engineering
To train the ML models, sequential lag features are engineered. Instead of absolute lat/lon coordinates, the models learn from relative kinematic changes:
* `prev_delta_lat`, `prev_delta_lon`: The displacement vector over the preceding interval.
* `prev_dt_hours`: The time elapsed during that preceding interval.

## 6. Machine Learning Models
Three baseline architectures are evaluated:
1. **Persistence:** The zero-knowledge baseline; assumes the velocity vector remains constant.
2. **Ridge Regression:** A linear baseline with L2 regularization.
3. **Gradient Boosting:** An ensemble tree-based method capable of nonlinear pattern recognition.
4. **GRU:** A recurrent neural network to capture deeper temporal dependencies.

## 7. Hybrid Approach
A Hybrid Physics + ML model is constructed. Due to the computational bottleneck of full OpenBerg simulations, a "physics proxy" (scaled persistence) is utilized as a mechanistic prior. A Gradient Boosting Regressor is then trained to predict the residual error between this prior and the ground truth.

## 8. Data Splitting
To strictly avoid temporal leakage and autocorrelation, data is split at the iceberg level. If an iceberg is in the Training set, all of its trajectory segments are in the Training set.

## 9. Evaluation
Models are evaluated on a held-out Test set. The primary metric is the Geodesic Error (calculated via the Haversine formula), which measures the absolute great-circle distance in kilometers between the predicted terminal point and the actual ground truth observation.

## 10. Results and Limitations
Results indicate that ML and Hybrid methods outperform pure persistence. However, limitations remain: the models currently rely on interpolated ground truth, assume constant geometry in physics proxy scaling, and lack direct integration of localized, on-the-fly environmental NetCDFs for the full ML population.

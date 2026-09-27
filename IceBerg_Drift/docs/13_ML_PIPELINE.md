# ML Pipeline

The machine learning pipeline predicts the next position of an iceberg based on its recent history.

## 1. Feature Engineering
Handled by `build_ml_dataset.py`.
Since icebergs possess immense inertia, their recent velocity is highly predictive.
* **Lag Features:** The script calculates the change in position (`prev_delta_lat`, `prev_delta_lon`) over the previous observation interval (`prev_dt_hours`).
* **Target Construction:** The model attempts to predict the next `target_delta_lat` and `target_delta_lon` over the `forecast_dt_hours` window.

## 2. Data Splitting
Handled by `create_iip_ml_split.py`.
* **Leakage Prevention:** If the same iceberg appears in both the training and test sets, the model might "memorize" specific historical storms or currents rather than learning general physics.
* **Iceberg-Level Split:** The dataset is split such that all observations of Iceberg A go into Train, and all observations of Iceberg B go into Test.

## 3. Scaling
* A `StandardScaler` is fit **only on the Training set**.
* It normalizes features to have zero mean and unit variance.
* The saved scaler (`models/baselines/ridge_scaler.joblib`) is applied to Validation and Test sets.

## 4. Model Training
Handled by `train_baseline_models.py`, `train_hybrid_model.py`, `train_gru_model.py`.
* Models optimize for Mean Squared Error (MSE) on the scaled target variables.
* Two separate regressors are often trained: one for Latitude Delta and one for Longitude Delta.

## 5. Prediction and Evaluation
Handled by `final_evaluation.py`.
* The models output predicted deltas in degrees.
* These are compared against the true target deltas.
* Because a 0.1 degree error at the equator is physically larger than a 0.1 degree error at 70°N, the evaluation script uses the **Haversine formula** to convert the angular errors into an absolute **Geodesic Error in kilometers**.

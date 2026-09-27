# How to Predict

## Question: "I have an iceberg observation. How do I get a prediction?"

**Important Clarification:** 
The current repository DOES NOT support simple, out-of-the-box prediction on a single, unseen raw iceberg observation via a unified CLI command. 

This is an **experimental prototype**, and the workflows are currently structured around bulk evaluation of historical test sets rather than operational real-time forecasting.

### Why?
1. **ML Model Requirement:** The ML pipeline requires *historical context*. To predict where an iceberg will go, you must supply at least two recent historical observations so the system can compute the `prev_delta_lat`, `prev_delta_lon`, and `prev_dt_hours` features.
2. **Physics Model Requirement:** The pure physics model (OpenBerg) requires downloading massive GLORYS and ERA5 NetCDF files bounding the iceberg's location and time. There is currently no automated script to fetch these on-the-fly for an arbitrary coordinate.

## Closest Existing Prediction Workflow

If you want to see a prediction in action, you must run it against the existing held-out test set:

1. Ensure the ML dataset is built (`python build_ml_dataset.py`).
2. Ensure models are trained (`python train_baseline_models.py`, `python train_hybrid_model.py`).
3. Run the evaluation script:
   ```powershell
   python final_evaluation.py
   ```
   This script internally loads the Test Set (which contains actual historical iceberg sequences), runs the models on the scaled features, outputs the predicted Delta Lat/Lon, and compares them against ground truth.

## Steps for Future Operational Implementation

To build a `predict.py` wrapper for this system in the future, a developer would need to:
1. Accept an array of recent observations (Time, Lat, Lon).
2. Format them into the exact feature schema required by the saved scalers (e.g. `ridge_scaler.joblib`).
3. Load the model (e.g. `gbr_lat.joblib`, `gbr_lon.joblib`).
4. Output the predicted deltas and add them to the last known position.

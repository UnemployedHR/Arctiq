# Developer Guide

If you are a developer picking up this project, here is where to look to modify specific components of the system.

## Where to modify Feature Engineering
* **File:** `build_ml_dataset.py`
* **Modifications:** If you want to add new ML features (e.g., rolling averages of velocity, acceleration, Coriolis parameters, or extracting local ocean current values from NetCDFs at the iceberg's location), do it here. Update the `feature_cols` list so downstream scripts know about the new features.

## Where to modify ML Models
* **Scikit-Learn baselines (Ridge, GBR):** `train_baseline_models.py`. You can swap Ridge for Lasso, Random Forest, or an SVM easily here.
* **GRU:** `train_gru_model.py`. Modify the PyTorch `IcebergGRU` class to add LSTM cells, attention layers, or change the hidden size.
* **Hybrid:** `train_hybrid_model.py`. The "physics prior" formula is located in the `add_physics_prior()` function.

## Where to modify Physics (OpenBerg)
* **File:** `real_run.py` or `dataset_config.py`.
* **Modifications:** 
  * To change iceberg mass/geometry, modify the parameters passed to `o.seed_elements()`.
  * To enable full 3D vertical profiling, change `o.set_config('drift:vertical_profile', True)` (Note: Ensure your NetCDF has multiple depth levels).
  * To tweak water drag or wind drag coefficients, use `o.set_config(...)` following OpenDrift documentation.

## Where to modify Evaluation Metrics
* **File:** `final_evaluation.py`
* **Modifications:** The geodesic error logic is in `geo_error_km_full()` (Haversine). If you want to add bearing error, cross-track error, or along-track error, add those metric functions here and update the `metrics_dict()`.

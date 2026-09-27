# File-by-File Reference

This document catalogs every important source, configuration, and execution file in the repository.

### `dataset_config.py`
**Purpose:** Centralizes configuration for GLORYS and ERA5 dataset ingestion. Defines dataset IDs, boundaries, target CF variable mappings for OpenBerg, and operational modes (Historical vs. Forecast).
**Inputs:** None directly.
**Outputs:** Python dictionaries (`HISTORICAL_OCEAN_DATASET`, `FORECAST_OCEAN_DATASET`, `ERA5_WIND_DATASET`).
**Used by:** `real_run.py`, `verify_glorys_3d.py`, etc.
**Required for:** Environmental Forcing setup.

### `real_run.py`
**Purpose:** An OpenBerg integration test that simulates an iceberg's trajectory (specifically Iceberg 20857) over a 24-hour period using downloaded GLORYS and ERA5 NetCDF files.
**Inputs:** `data/copernicus/glorys_iceberg_20857/...nc`, `data/wind/iceberg_20857/...nc`.
**Outputs:** `data/results/iceberg_20857/real_run_24h.nc`, `.csv`, `.png`.
**Required for:** Physics Simulation (Diagnostics / Prototype reference).

### `build_ml_dataset.py`
**Purpose:** Feature engineering pipeline. Transforms raw sequential iceberg observations into structured Lag Features (`prev_delta_lat`, `prev_delta_lon`, `prev_dt_hours`) and computes targets for the ML models.
**Outputs:** `data/ml/final_ml_dataset.parquet`, `data/ml/ml_dataset_config.json`.
**Required for:** ML pipeline (Training).

### `create_iip_ml_split.py` / `audit_iip_ml_split.py`
**Purpose:** Performs a randomized Train/Validation/Test split strictly separated by Iceberg ID to prevent temporal leakage. The audit script verifies that no iceberg exists in multiple splits.
**Required for:** ML pipeline (Training).

### `train_baseline_models.py`
**Purpose:** Trains the Persistence, Ridge Regression, and Gradient Boosting baselines on the training split and evaluates them on the validation split. 
**Outputs:** `.joblib` files in `models/baselines/`, `baseline_results.json`, `baseline_error_distributions.png`.
**Required for:** ML pipeline (Training).

### `train_gru_model.py`
**Purpose:** Trains a PyTorch-based Gated Recurrent Unit (GRU) model using sequences of historical iceberg movements.
**Outputs:** `best_model.pt`, scalers, `gru_results.json` in `models/gru/`.
**Required for:** ML pipeline (Training).

### `train_hybrid_model.py`
**Purpose:** Trains a Hybrid Physics + ML model. Uses a scaled-persistence physics prior and trains a Gradient Boosting Regressor to predict the residual error.
**Outputs:** `.joblib` files, `hybrid_results.json` in `models/hybrid/`.
**Required for:** ML pipeline (Training).

### `final_evaluation.py`
**Purpose:** The final evaluation harness. Loads all trained models (Ridge, GBR, GRU, Hybrid) and evaluates them against the held-out Test split.
**Inputs:** Parquet test split, saved models.
**Outputs:** `models/final_test_results.json`, `figures/model_comparison.png`, `figures/error_distributions_all.png`.
**Required for:** ML pipeline (Evaluation).

### `generate_reports.py`
**Purpose:** Consumes the JSON result files from evaluations and outputs formatted Markdown summaries.
**Outputs:** `reports/*.md`.
**Required for:** Reporting.

### Experimental / Diagnostic Scripts
* `diagnose_grounding_v2.py`: Diagnostics for landmask/grounding collisions in OpenDrift.
* `forcing_attribution.py` / `forcing_attribution_7day.py`: Tests the impact of turning wind/currents on/off individually in OpenBerg.
* `trajectory_bridge_analysis.py`: Evaluates interpolation divergence.
* `openberg_vector_sanity_test.py`: Force-balance sanity checks.

# API / CLI Reference

**Important Status:** No production API is currently implemented.

This project operates as a collection of standalone Python scripts executed via the CLI. There is no unified `predict` command or REST API.

## Main Scripts Reference

### `python build_ml_dataset.py`
* **Command:** `python build_ml_dataset.py`
* **Arguments:** None. (Reads paths internally).
* **Required Input:** Cleaned IIP trajectory data in `data/` or internal arrays.
* **Output:** `data/ml/final_ml_dataset.parquet`

### `python train_baseline_models.py`
* **Command:** `python train_baseline_models.py`
* **Arguments:** None.
* **Required Input:** Parquet splits from `create_iip_ml_split.py`.
* **Output:** Trained `.joblib` models in `models/baselines/`.

### `python real_run.py`
* **Command:** `python real_run.py`
* **Arguments:** None.
* **Required Input:** NetCDF files defined in script variables (`copernicus_file`, `era5_wind_file`).
* **Output:** NetCDF and CSV simulations in `data/results/iceberg_20857/`.

### `python final_evaluation.py`
* **Command:** `python final_evaluation.py`
* **Arguments:** None.
* **Required Input:** Trained `.joblib` and `.pt` models; Test split Parquet.
* **Output:** `models/final_test_results.json` and figures.

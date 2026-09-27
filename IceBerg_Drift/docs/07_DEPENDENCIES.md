# Dependencies

This project relies on a standard scientific Python stack, Machine Learning libraries, and specialized oceanographic simulation tools.

## Core Dependency Inventory

| Dependency | Purpose | Required/Optional | Used By |
|------------|---------|-------------------|---------|
| `numpy` | Numerical operations, arrays | Required | All |
| `pandas` | Data manipulation, CSV parsing | Required | Data Prep, ML pipeline |
| `scikit-learn` | Ridge Regression, GBR, metrics | Required | ML pipeline (`train_baseline_models.py`) |
| `xgboost` | Gradient Boosting Regressor (fallback to sklearn GBR if missing) | Recommended | ML pipeline |
| `torch` (PyTorch)| GRU sequence modeling | Required | `train_gru_model.py` |
| `matplotlib` | Plotting results, error distributions | Required | Evaluation scripts |
| `opendrift` | Core physics simulation | Required for Physics | `real_run.py`, OpenBerg |
| `xarray` | NetCDF parsing for environmental data | Required for Physics | `dataset_config.py`, OpenDrift |
| `netCDF4` | NetCDF binary backend | Required for Physics | OpenDrift |
| `pyarrow` / `fastparquet` | Reading/Writing Parquet ML dataset files | Required | ML Pipeline |
| `joblib` | Model and Scaler serialization | Required | ML Pipeline |

## Installation

A generated `requirements.txt` is available in the root directory.
Install using:
```powershell
pip install -r requirements.txt
```

### PyTorch Warning
PyTorch can be heavy. If you only intend to run the physics simulations (OpenBerg) or the Scikit-Learn baselines, you can technically run those scripts without PyTorch installed, though `train_gru_model.py` will fail.

### OpenDrift Compatibility
OpenDrift occasionally updates reader protocols. The configuration in `dataset_config.py` uses `reader_netCDF_CF_generic`, which requires `xarray` and `netCDF4`.

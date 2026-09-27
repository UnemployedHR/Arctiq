# Documentation Audit

## Overview
This document certifies that the documentation provided in the `docs/` folder accurately reflects the codebase as found in the repository at the time of the audit.

## Files Inspected
* `dataset_config.py`
* `real_run.py`
* `build_ml_dataset.py`
* `train_baseline_models.py`
* `train_hybrid_model.py`
* `train_gru_model.py`
* `final_evaluation.py`
* `generate_reports.py`
* `diagnose_grounding_v2.py`
* `forcing_attribution_7day.py`
* Multiple existing `.md` reports (`FORCING_ATTRIBUTION_7DAY.md`, `GROUNDING_DIAGNOSTIC_V2.md`, etc.)

## Datasets Detected
* IIP Catalog (processed into `final_ml_dataset.parquet`).
* Copernicus GLORYS (referenced in `dataset_config.py`, expected in `data/copernicus/`).
* ERA5 Wind (referenced in `dataset_config.py`, expected in `data/wind/`).

## Models Detected
* Persistence
* Ridge Regression
* Gradient Boosting Regressor (XGBoost / scikit-learn)
* GRU (PyTorch)
* Hybrid Physics + ML
* Pure Physics (OpenBerg) (Reference only)

## Dependencies Detected
* `numpy`, `pandas`, `scikit-learn`, `xgboost`, `torch`, `matplotlib`, `opendrift`, `xarray`, `netCDF4`, `pyarrow`, `joblib`.

## Commands Verified
* All commands listed in `10_HOW_TO_RUN.md` directly map to root `.py` execution scripts.

## Limitations Verified
* The prototype status is explicitly stated in `01_PROJECT_OVERVIEW.md`, `11_HOW_TO_PREDICT.md`, and `22_LIMITATIONS.md`.
* The lack of a true, single-observation operational prediction script (`predict.py`) has been documented and not fabricated.
* The limitation of the Hybrid model using a "scaled-persistence" physics proxy instead of a full OpenBerg numerical integration for the entire ML population is correctly stated.

## Final Status
* **Documentation Location:** All generated markdown files are placed within the `docs/` folder.
* **Integrity:** The documentation strictly describes the project *as-is*, without inventing unavailable functionality.

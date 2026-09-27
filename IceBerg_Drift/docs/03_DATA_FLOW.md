# Data Flow

This document maps the complete journey of data through the Iceberg Trajectory Prediction System.

## The Data Journey

1. **Raw Data Ingestion:** The system begins with raw IIP iceberg observation data and downloaded environmental NetCDF files (GLORYS/ERA5).
2. **Trajectory Construction:** Raw observations are grouped by iceberg ID and sorted temporally.
3. **Feature Engineering:** Sequences are constructed. Delta latitudes, delta longitudes, and time deltas are calculated.
4. **Dataset Creation:** The structured features are saved into a Parquet file.
5. **Data Split:** The dataset is split into Train/Validation/Test sets *by iceberg ID* to ensure no data leakage.
6. **Model Training:** Baselines, GRU, and Hybrid models ingest the train/val splits.
7. **Prediction & Evaluation:** The models predict displacements on the held-out test set, and geodesic errors are computed.
8. **Visualization:** Matplotlib scripts generate error distributions and trajectory bridges.

## Data Flow Table

| Stage | Input | Script/File | Output | Format |
|-------|-------|-------------|--------|--------|
| **Data Preparation** | Raw IIP / Env Data | `prepare_iip_20857.py`, `prepare_iip_2021_catalog.py` | Cleaned observations | CSV |
| **Trajectory Assembly** | Cleaned Observations | `build_trajectory_segments.py` | Trajectory sequences | CSV / internal |
| **Feature Engineering** | Trajectory sequences | `build_ml_dataset.py` | ML dataset | Parquet |
| **Data Splitting** | ML dataset | `create_iip_ml_split.py`, `audit_iip_ml_split.py` | Split assignments | Parquet / JSON |
| **Physics Simulation** | GLORYS, ERA5, Seed Loc | `real_run.py`, `historical_validation.py` | Physics Trajectory | NetCDF (.nc), CSV |
| **ML Training** | Train/Val split (Parquet) | `train_baseline_models.py`, `train_gru_model.py`, `train_hybrid_model.py` | Trained Models | .joblib, .pt |
| **Evaluation** | Test split, Trained Models | `final_evaluation.py` | Error Metrics | JSON, PNG |
| **Reporting** | JSON results, Model metadata | `generate_reports.py` | Summary Reports | Markdown (.md) |

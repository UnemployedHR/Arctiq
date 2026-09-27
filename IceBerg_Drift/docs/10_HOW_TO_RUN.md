# How to Run

This document provides the exact commands for running the major workflows in the Iceberg Trajectory Prediction System.

All commands assume you have activated the virtual environment and are located in the project root (`C:\...\iceberg_project`).

## A. Data Preparation & Feature Engineering
*(This generates the ML features from raw data)*
```powershell
# Clean and prepare specific data
python prepare_iip_20857.py
python prepare_iip_2021_catalog.py

# Build full sequences and features
python build_ml_dataset.py

# Split data into train/val/test
python create_iip_ml_split.py
python audit_iip_ml_split.py
```

## B. Model Training
*(This trains the ML models on the generated dataset)*
```powershell
# Train Persistence, Ridge, and Gradient Boosting
python train_baseline_models.py

# Train GRU (Requires PyTorch)
python train_gru_model.py

# Train Hybrid Physics + ML model
python train_hybrid_model.py
```

## C. Physics Simulation (OpenBerg)
*(Runs a single-iceberg 24h physics test — requires NetCDF files)*
```powershell
python real_run.py
```

## D. Physics / Forcing Experiments
*(Runs diagnostic attribution tests for current vs. wind)*
```powershell
python forcing_attribution.py
python forcing_attribution_7day.py
```

## E. Final Evaluation
*(Evaluates all trained models on the held-out Test set)*
```powershell
python final_evaluation.py
```

## F. Report Generation
*(Aggregates JSON metrics into Markdown reports)*
```powershell
python generate_reports.py
```

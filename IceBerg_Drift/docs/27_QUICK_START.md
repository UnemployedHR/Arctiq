# Quick Start Guide

Welcome to the Iceberg Trajectory Prediction System. 

## What is this project?
This is a prototype system that attempts to predict where an iceberg will drift based on its recent historical path and environmental ocean/wind data. It evaluates pure physics simulation (OpenBerg) alongside Machine Learning approaches.

## 1. Installation
Open PowerShell and run:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Where do I put data?
* **Raw IIP Data / ML Parquet files** go in `data/ml/`.
* **Ocean Current NetCDFs** (e.g. GLORYS) go in `data/copernicus/`.
* **Wind NetCDFs** (e.g. ERA5) go in `data/wind/`.

## 3. How do I run it?
To run the ML training pipeline:
```powershell
python build_ml_dataset.py
python create_iip_ml_split.py
python train_baseline_models.py
```

To run a single-iceberg physics simulation (requires NetCDF data in `data/`):
```powershell
python real_run.py
```

## 4. How do I make a prediction?
Because this is a prototype, there is no single `predict(lat, lon)` command. The system currently predicts in bulk on a test dataset. To see it in action:
```powershell
python final_evaluation.py
```

## 5. Where is the output?
* Trained models are saved in the `models/` folder.
* Evaluation metrics (Mean error, RMSE) are saved as JSONs in `models/` and converted to Markdown in `reports/`.
* Plots and charts are generated in `figures/`.

# Iceberg Trajectory Prediction System

## Project Overview
This project is an advanced prototype designed to predict the trajectories of drifting icebergs. It explores a hybrid methodology, evaluating purely physics-based simulations (OpenBerg/OpenDrift) against data-driven Machine Learning (ML) models (Ridge, Gradient Boosting, GRU) to forecast iceberg displacements based on historical observations and environmental forcing.

## Problem
Traditional physics models require high-resolution oceanographic/atmospheric data and precise iceberg geometries, which are often unavailable or deeply uncertain in operational scenarios. Pure ML models can learn empirical drift patterns but lack physical constraints.

## Solution
This repository implements a multi-model approach to benchmark trajectory prediction. It includes a physics proxy combined with an ML residual corrector (Hybrid Model) to explore how injecting mechanistic priors improves data-driven forecasts.

## Architecture
The system consists of a data preparation pipeline, an environmental forcing configuration (GLORYS and ERA5), an ML feature engineering layer (calculating sequential kinematics), training workflows, and a comprehensive evaluation harness to compare geodesic prediction errors.

## Technologies
* **Python 3**
* **Physics:** OpenDrift (OpenBerg), xarray, netCDF4
* **Machine Learning:** Scikit-Learn, XGBoost, PyTorch
* **Data:** Pandas, NumPy, PyArrow

## Datasets
* **International Ice Patrol (IIP):** Historical observations.
* **Copernicus GLORYS12V1:** Daily ocean currents.
* **ECMWF ERA5:** Hourly wind data.

## Installation
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Quick Start
To train the baseline models and evaluate them on the generated splits:
```powershell
python build_ml_dataset.py
python create_iip_ml_split.py
python train_baseline_models.py
python final_evaluation.py
```

## Prediction
**Important:** This system is an experimental prototype. True unseen real-world prediction from a single arbitrary observation is *not yet implemented* because the models require sequential lag features (`prev_delta_lat`, etc.). To see predictions, run `python final_evaluation.py` which evaluates the models in bulk on the historical test set.

## Training
Use the `train_*.py` scripts to train specific architectures.
```powershell
python train_baseline_models.py
python train_gru_model.py
python train_hybrid_model.py
```

## Physics Simulation
A 24-hour OpenBerg integration test can be run via:
```powershell
python real_run.py
```
*(Requires downloading the relevant NetCDF files to the `data/` directory).*

## Evaluation & Results
Evaluation computes the geodesic error (in km) between the predicted terminal point and the actual ground truth. Results are automatically aggregated into JSONs in `models/` and Markdown reports in `reports/`.

## Folder Structure
* `data/` - Raw datasets, ML features, and simulation outputs.
* `docs/` - Comprehensive documentation (see below).
* `figures/` - Generated plots.
* `models/` - Saved weights, scalers, and JSON metrics.
* `reports/` - Auto-generated markdown summaries.

## Documentation
Complete, file-by-file, technical documentation is available in the `docs/` folder:
* [01 Project Overview](docs/01_PROJECT_OVERVIEW.md)
* [02 System Architecture](docs/02_SYSTEM_ARCHITECTURE.md)
* [03 Data Flow](docs/03_DATA_FLOW.md)
* [04 Folder Structure](docs/04_FOLDER_STRUCTURE.md)
* [05 File-by-File Reference](docs/05_FILE_BY_FILE_REFERENCE.md)
* [06 Setup Guide](docs/06_SETUP_GUIDE.md)
* [10 How to Run](docs/10_HOW_TO_RUN.md)
* [11 How to Predict](docs/11_HOW_TO_PREDICT.md)
* [13 ML Pipeline](docs/13_ML_PIPELINE.md)
* [15 Physics Model](docs/15_PHYSICS_MODEL.md)
* [22 Limitations](docs/22_LIMITATIONS.md)

*See the `docs/` folder for the full 29-document suite.*

## Limitations
* No operational API or single-command inference for unseen real-world data.
* Sparse historical IIP observations require significant temporal interpolation.
* The Hybrid model utilizes a scaled-persistence physics proxy rather than a full numerical OpenBerg integration due to data download bottlenecks.

## Reproducibility
The ML pipeline is heavily seeded (`RANDOM_SEED = 42`). Reproducing exact metrics requires running the data splitting and training scripts sequentially in the correct environment.

## Future Work
* Automated API ingestion for GLORYS and ERA5.
* Real-time probabilistic forecasting using Monte Carlo dropout.
* Dynamic geometric degradation modeling for the physics engine.

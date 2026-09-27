# Folder Structure

The repository relies on a specific structure to organize data, scripts, models, and generated outputs.

```text
PROJECT_ROOT/
│
├── data/                       # Contains all input datasets and generated features
│   ├── copernicus/             # GLORYS ocean current NetCDF files
│   ├── wind/                   # ERA5 wind NetCDF files
│   ├── ml/                     # ML datasets, splits, and config (Parquet, JSON)
│   └── results/                # Output simulations and CSV dumps
│
├── docs/                       # ALL official documentation (this folder)
│
├── figures/                    # Generated visualization outputs (PNG)
│
├── models/                     # Saved model artifacts and evaluation JSONs
│   ├── baselines/              # Ridge, GBR, and Scaler joblib files
│   ├── gru/                    # PyTorch .pt model, scalers, architecture info
│   └── hybrid/                 # Hybrid model joblibs and config
│
├── reports/                    # Auto-generated markdown reports from `generate_reports.py`
│
├── venv/                       # Python virtual environment (if created locally)
│
├── scratch/                    # Scratchpad directory for temporary testing
│
└── *.py / *.md                 # Root-level execution scripts and markdown specs
```

## Folder Details

* **`data/`**: The core data hub. User MUST place raw/downloaded NetCDF and IIP CSV files here following the expected paths defined in scripts. Generated Parquet datasets from `build_ml_dataset.py` also live here. **Required for training and physics simulation.**
* **`docs/`**: Hand-written and generated documentation representing the state of the project.
* **`figures/`**: Purely generated output. Contains error distribution histograms, trajectory divergence charts, and comparison bar plots. Safe to delete (will be regenerated).
* **`models/`**: Stores binary weights, architectures, scalers, and JSON evaluation dumps. **Required for prediction.**
* **`reports/`**: Generated textual markdown reports summarizing model performance and validation.
* **Root Python files**: The primary execution points for the ML pipeline and physics simulations. Users run these scripts directly from the root.

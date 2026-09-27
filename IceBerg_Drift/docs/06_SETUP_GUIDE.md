# Setup Guide

This guide describes how to set up the Iceberg Trajectory Prediction System on a fresh Windows machine using PowerShell.

## 1. System Requirements
* Windows 10/11
* Python 3.9 - 3.11 (3.12+ may have compatibility issues with older PyTorch/xarray builds depending on your compiler).
* Git (Optional, for cloning).

## 2. Installation Steps

Open Windows PowerShell and run the following commands:

**Step 2.1: Navigate to the project directory**
```powershell
cd C:\path\to\iceberg_project
```

**Step 2.2: Create and activate a Virtual Environment**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If execution policies block the activation script, run: `Set-ExecutionPolicy Unrestricted -Scope CurrentUser`)*

**Step 2.3: Upgrade pip and install dependencies**
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```
*(Note: If PyTorch CPU is preferred for non-GPU machines, you may need to install it explicitly via: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`)*

## 3. Verifying Installation

**Verify core ML libraries:**
```powershell
python -c "import pandas, numpy, sklearn, torch, xgboost; print('ML dependencies OK')"
```

**Verify Physics / OpenDrift:**
```powershell
python -c "import opendrift, xarray, netCDF4; print('Physics dependencies OK')"
```

## 4. Run a Basic Sanity Test
To ensure the pipeline is functioning, run the final evaluation script (assuming models are already trained and present in the `models/` folder):
```powershell
python final_evaluation.py
```
This should load the models and output error metrics.

To test OpenBerg physics simulation (requires NetCDF files in `data/copernicus` and `data/wind`):
```powershell
python real_run.py
```

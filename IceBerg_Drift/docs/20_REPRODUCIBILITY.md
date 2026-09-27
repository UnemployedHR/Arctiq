# Reproducibility

Reproducing the exact evaluation metrics reported in `18_RESULTS.md` requires strict adherence to the environment and data splits.

## 1. Environment
* Python version: 3.9 - 3.11
* Exact package versions (as listed in `requirements.txt`). Different versions of scikit-learn or XGBoost may result in slightly different tree architectures and split decisions.

## 2. Data Splits and Random Seeds
* The project strictly enforces `RANDOM_SEED = 42` across all ML training and splitting scripts (`train_baseline_models.py`, `train_hybrid_model.py`, `train_gru_model.py`, `create_iip_ml_split.py`).
* This ensures that the exact same icebergs are assigned to Train/Val/Test sets on every run.
* **Warning:** If `build_ml_dataset.py` is run on a differently-sorted or newly-downloaded raw IIP CSV, the row indices might shift, altering the sequence generation and subsequently the exact metrics.

## 3. Reproduction Steps
1. Delete `data/ml/final_ml_dataset.parquet`.
2. Delete the contents of `models/`.
3. Run `python build_ml_dataset.py`
4. Run `python create_iip_ml_split.py`
5. Run `python train_baseline_models.py`
6. Run `python train_hybrid_model.py`
7. Run `python final_evaluation.py`

Compare the outputs in `models/final_test_results.json` against the documented results.

## Potential Reproduction Barriers
* **Hardware:** PyTorch (GRU) results might differ slightly between CPU and CUDA executions due to non-deterministic operations in some RNN kernels.
* **External Data:** Copernicus operates a sliding window on operational datasets. If attempting to reproduce physics runs using Mode 2 (Forecast), historical NetCDFs may no longer be available. Mode 1 (Historical) should be static.

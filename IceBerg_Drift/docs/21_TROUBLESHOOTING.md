# Troubleshooting

This document outlines known issues discovered during the development of this prototype.

## 1. OpenDrift/OpenBerg "No Data" or "Out of Bounds" Errors
* **Problem:** OpenDrift throws an error that the particle is outside the reader's spatial or temporal domain.
* **Cause:** The NetCDF files (`GLORYS` or `ERA5`) downloaded do not completely cover the iceberg's requested seed location, time, or the area it subsequently drifted into.
* **Solution:** Re-download the NetCDF files with a wider bounding box (e.g., +/- 10 degrees lat/lon) and a longer time window (+2 days).

## 2. Missing `x_wind` / `y_wind` in OpenBerg
* **Problem:** OpenBerg initialization fails stating required variables are missing from the wind reader.
* **Cause:** ERA5 names variables `u10` and `v10`. OpenBerg expects `x_wind` and `y_wind`.
* **Solution:** Ensure the `standard_name_mapping` is passed when creating the reader:
  `reader_netCDF_CF_generic.Reader(file, standard_name_mapping={'u10': 'x_wind', 'v10': 'y_wind'})`

## 3. Iceberg Suddenly Stops Moving (Grounding)
* **Problem:** Simulated iceberg velocity drops to zero near the coast.
* **Cause:** OpenDrift's landmask detection. The 0.083-degree resolution of GLORYS creates a coarse "blocky" coastline. Icebergs close to the shore in reality may hit the simulated landmask.
* **Solution:** Diagnostics (e.g., `diagnose_grounding_v2.py`) suggest disabling landmask interactions (`drift:use_landmask = False`) if focusing purely on open-water kinematics, or using higher-resolution local bathymetry.

## 4. PyTorch CPU/CUDA Issues
* **Problem:** `train_gru_model.py` crashes with CUDA memory or driver errors.
* **Cause:** Incompatible PyTorch compilation for your local GPU.
* **Solution:** For evaluation purposes, uninstall PyTorch and reinstall the CPU-only version, or set `device = 'cpu'` manually in the script.

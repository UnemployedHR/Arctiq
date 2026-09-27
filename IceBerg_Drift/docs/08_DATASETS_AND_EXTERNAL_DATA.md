# Datasets and External Data

The project utilizes several external datasets for both historical ML training and physics simulations. 

## 1. International Ice Patrol (IIP) Dataset
* **Provider:** US Coast Guard / IIP
* **Purpose:** Provides historical iceberg observations (Ground Truth).
* **Format:** CSV / Parquet
* **Usage:** Used to generate the `final_ml_dataset.parquet`.
* **Variables:** Iceberg ID, Timestamp, Latitude, Longitude, Size, Shape.
* **Status in Repo:** The raw CSVs are processed into intermediate Parquet files.

## 2. Copernicus GLORYS12V1 (Historical Ocean)
* **Provider:** Copernicus Marine Environment Monitoring Service (CMEMS)
* **Dataset ID:** `cmems_mod_glo_phy_my_0.083deg_P1D-m`
* **Purpose:** Historical hindcast of ocean currents (Mode 1 in `dataset_config.py`).
* **Format:** NetCDF (`.nc`)
* **Variables:** `uo` (eastward_sea_water_velocity), `vo` (northward_sea_water_velocity).
* **Resolution:** Daily means, 0.083 degrees.
* **Usage:** Read by OpenDrift in `real_run.py`.

## 3. Copernicus GLO12 Analysis/Forecast (Operational Ocean)
* **Dataset ID:** `cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m`
* **Purpose:** Future operational forecast of ocean currents (Mode 2).
* **Format:** NetCDF
* **Usage:** Defined in config but primarily meant for real-time future operational forecasting.

## 4. ERA5 (Wind Reanalysis)
* **Provider:** Copernicus Climate Data Store (CDS)
* **Dataset ID:** `reanalysis-era5-single-levels`
* **Purpose:** Historical surface wind forcing.
* **Format:** NetCDF (`.nc`)
* **Variables:** `u10` (eastward wind), `v10` (northward wind).
* **Resolution:** Hourly.
* **Usage:** Added as a reader to OpenBerg.

## Downloading Data
*This project does not include massive raw NetCDF files in the repository due to size constraints.* 
To run full physics simulations on new icebergs, users must manually download the bounding box NetCDFs from Copernicus/CDS and place them in:
* `data/copernicus/`
* `data/wind/`
The API configurations and credentials for CMEMS and CDS must be configured locally in `~/.netrc` and `~/.cdsapirc` as per `dataset_config.py`.

# Dataset Compatibility Report for OpenBerg Real-Data Forcing

**Project:** OpenDrift / OpenBerg Iceberg Trajectory Simulation  
**Environment:** OpenDrift 1.14.11 · Python venv · Windows  
**Updated:** 2026-09-26  
**Status:** Pre-download — no data downloaded yet  

---

## Two Distinct Modes

| Mode | Purpose | Dataset | Product |
|---|---|---|---|
| **MODE 1 — Historical / Validation** | Hindcast, validation, comparison with past observations | GLORYS12V1 | `GLOBAL_MULTIYEAR_PHY_001_030` |
| **MODE 2 — Operational Forecast** | Future iceberg trajectory prediction | GLO12 Operational | `GLOBAL_ANALYSISFORECAST_PHY_001_024` |

These two ocean products use the **same model physics, same resolution, same variable names, and same CF conventions**, but differ critically in **time coverage and purpose**.

---

## Dataset A — Historical / Validation: GLORYS12V1

### Product Overview

| Field | Value |
|---|---|
| **Product name** | Global Ocean Physics Reanalysis |
| **Product ID** | `GLOBAL_MULTIYEAR_PHY_001_030` |
| **Dataset ID (daily — uo/vo)** | `cmems_mod_glo_phy_my_0.083deg_P1D-m` |
| **Model** | GLORYS12V1 (Mercator Ocean International) |
| **Nature** | **Reanalysis** — retrospective best-estimate assimilating all available observations |
| **Official page** | `https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030/description` |

### Variables

| NetCDF var | CF standard_name | Units | Dims | OpenBerg target |
|---|---|---|---|---|
| `uo` | `eastward_sea_water_velocity` | m s⁻¹ | 4D (t,z,lat,lon) | `x_sea_water_velocity` ✅ |
| `vo` | `northward_sea_water_velocity` | m s⁻¹ | 4D (t,z,lat,lon) | `y_sea_water_velocity` ✅ |
| `thetao` | `sea_water_potential_temperature` | degrees_C | 4D | `sea_water_temperature` (aliased) |
| `so` | `sea_water_salinity` | PSU | 4D | `sea_water_salinity` |
| `zos` | `sea_surface_height_above_geoid` | m | 3D (t,lat,lon) | `sea_surface_height` (aliased) |
| `siconc` | `sea_ice_area_fraction` | 1 (0–1) | 3D | `sea_ice_area_fraction` |
| `sithick` | `sea_ice_thickness` | m | 3D | `sea_ice_thickness` |
| `usi` | `eastward_sea_ice_velocity` | m s⁻¹ | 3D | `sea_ice_x_velocity` |
| `vsi` | `northward_sea_ice_velocity` | m s⁻¹ | 3D | `sea_ice_y_velocity` |
| `deptho` | `sea_floor_depth_below_geoid` | m | 2D (lat,lon) | `sea_floor_depth_below_sea_level` (aliased) |

### Coordinates

| Role | Name | standard_name | Units | Notes |
|---|---|---|---|---|
| Time | `time` | `time` | `hours since 1950-01-01` | CF-compliant, decoded by reader |
| Latitude | `latitude` | `latitude` | `degrees_north` | 1D regular |
| Longitude | `longitude` | `longitude` | `degrees_east` | 1D regular |
| Depth | `depth` | `depth` | `m` | 50 levels, `positive: down` |

### Specifications

| Property | Value |
|---|---|
| **Horizontal resolution** | 1/12° × 1/12° (~8 km) |
| **Temporal resolution** | **Daily means** (`P1D`) |
| **Vertical levels** | 50 (0.494 m to 5727 m) |
| **Temporal coverage** | **1993-01-01 to present** (~1 week latency) |
| **Spatial coverage** | Global (-180/+180°, -80/+90°) |
| **Nature** | Reanalysis — NOT a forecast |

### OpenDrift Reader Compatibility

| Reader | Status | Notes |
|---|---|---|
| `reader_copernicusmarine` | ✅ **Direct streaming** | Requires `copernicusmarine` package + CMEMS account |
| `reader_netCDF_CF_generic` | ✅ **Downloaded file** | No extra packages needed |
| `standard_name_mapping` needed? | ❌ **None** | All variables carry correct CF `standard_name` attributes |

> **Alias chain used automatically by basereader:**  
> `eastward_sea_water_velocity` → `x_sea_water_velocity`  
> `northward_sea_water_velocity` → `y_sea_water_velocity`  
> `sea_water_potential_temperature` → `sea_water_temperature`  
> `sea_surface_height_above_geoid` → `sea_surface_height`  
> `sea_floor_depth_below_geoid` → `sea_floor_depth_below_sea_level`  
> `eastward_sea_ice_velocity` → `sea_ice_x_velocity`  

### Suitability for North Atlantic / Greenland Sea Icebergs

✅ **Highly suitable for validation.** Covers all iceberg-bearing regions. 1/12° resolution resolves mesoscale eddies. Includes sea ice. 50 depth levels support melting calculations.  
⚠️ **Cannot be used for future forecasts** — it only covers the past (reanalysis).

---

## Dataset B — Operational Forecast: GLO12 Analysis/Forecast

### Product Overview

| Field | Value |
|---|---|
| **Product name** | Global Ocean Physics Analysis and Forecast |
| **Product ID** | `GLOBAL_ANALYSISFORECAST_PHY_001_024` |
| **Dataset ID (3D daily currents — uo/vo)** | `cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m` |
| **Dataset ID (6-hourly currents)** | `cmems_mod_glo_phy-cur_anfc_0.083deg_PT6H-i` |
| **Dataset ID (hourly surface currents)** | `cmems_mod_glo_phy_anfc_merged-uv_PT1H-i` |
| **Model** | GLO12 (Mercator Ocean International) |
| **Nature** | **Analysis + 10-day forecast**, updated daily |
| **Official page** | `https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description` |

> **Important distinction on dataset IDs:**  
> `cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m` → **3D daily uo/vo** (the correct one for iceberg drift)  
> `cmems_mod_glo_phy_anfc_0.083deg_P1D-m` → **2D daily fields** (SSH, SST, sea ice — does NOT contain 3D uo/vo)  
> Use the one with `-cur-` in the name for current vectors.

### Variables (identical names to GLORYS12)

| NetCDF var | CF standard_name | Units | Dims | OpenBerg target |
|---|---|---|---|---|
| `uo` | `eastward_sea_water_velocity` | m s⁻¹ | 4D (t,z,lat,lon) | `x_sea_water_velocity` ✅ |
| `vo` | `northward_sea_water_velocity` | m s⁻¹ | 4D (t,z,lat,lon) | `y_sea_water_velocity` ✅ |
| `thetao` | `sea_water_potential_temperature` | degrees_C | 4D | `sea_water_temperature` |
| `so` | `sea_water_salinity` | PSU | 4D | `sea_water_salinity` |
| `zos` | `sea_surface_height_above_geoid` | m | 3D | `sea_surface_height` |
| `siconc` | `sea_ice_area_fraction` | 1 (0–1) | 3D | `sea_ice_area_fraction` |
| `sithick` | `sea_ice_thickness` | m | 3D | `sea_ice_thickness` |
| `usi` | `eastward_sea_ice_velocity` | m s⁻¹ | 3D | `sea_ice_x_velocity` |
| `vsi` | `northward_sea_ice_velocity` | m s⁻¹ | 3D | `sea_ice_y_velocity` |

> The variable names and CF standard_names are **identical** between GLORYS12 and this operational product. Code written for one works for the other.

### Coordinates (same as GLORYS12)

| Role | Name | standard_name | Units |
|---|---|---|---|
| Time | `time` | `time` | `hours since 1950-01-01` |
| Latitude | `latitude` | `latitude` | `degrees_north` |
| Longitude | `longitude` | `longitude` | `degrees_east` |
| Depth | `depth` | `depth` | `m`, `positive: down` |

### Specifications

| Property | Value |
|---|---|
| **Horizontal resolution** | 1/12° × 1/12° (~8 km) — same as GLORYS12 |
| **Temporal resolution (3D daily)** | **Daily means** for full 3D uo/vo |
| **Temporal resolution (6-hourly)** | 6-hourly instantaneous surface currents |
| **Temporal resolution (hourly)** | 1-hourly surface-only SMOC currents |
| **Vertical levels** | **50** (0–5500 m) |
| **Temporal coverage** | **~2 years sliding window** + 10-day forecast from today |
| **Spatial coverage** | Global |
| **Nature** | **Analysis (past 2 years) + Forecast (next 10 days)** |

> ⚠️ **Sliding window:** Unlike GLORYS12 which covers 1993–present, the forecast product maintains only a ~2-year rolling archive. It is **not** suitable for historical simulations older than ~2 years. Use GLORYS12 for those.

### Recommended Dataset ID for Iceberg Drift

For OpenBerg's mandatory `x_sea_water_velocity` / `y_sea_water_velocity`:

```
cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m
```
This provides **full 3D uo/vo** (50 depth levels) at daily resolution — optimal for 48-hour iceberg trajectory forecasts.

For higher-frequency forcing, use `PT6H-i` (6-hourly) or `PT1H-i` (surface-only hourly), though the surface-only SMOC product includes tidal and wave contributions which may not match OpenBerg's current model assumptions.

### OpenDrift Reader Compatibility

| Reader | Status | Notes |
|---|---|---|
| `reader_copernicusmarine` | ✅ **Direct streaming** | Preferred for real-time forecasts |
| `reader_netCDF_CF_generic` | ✅ **Downloaded file** | Same as GLORYS12 |
| `standard_name_mapping` needed? | ❌ **None** | Identical CF attributes to GLORYS12 |

### Suitability for North Atlantic / Greenland Sea Icebergs

✅ **The correct dataset for operational forecasting.**  
✅ Same resolution and variables as GLORYS12 — code is fully portable.  
✅ 10-day forecast horizon is appropriate for iceberg trajectory prediction.  
⚠️ Not suitable for simulations >~2 years in the past (use GLORYS12 instead).

---

## Dataset C — Wind: ERA5 Hourly Single Levels

### Product Overview

| Field | Value |
|---|---|
| **Dataset name** | ERA5 hourly data on single levels |
| **CDS dataset ID** | `reanalysis-era5-single-levels` |
| **Model** | ERA5 (ECMWF) |
| **Nature** | **Reanalysis** |
| **Official page** | `https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels` |
| **API setup** | `https://cds.climate.copernicus.eu/how-to-api` |

> **Note on ERA5 for forecast mode:** ERA5 is a reanalysis and does **not** provide future forecasts. For fully operational forecast mode, pair the CMEMS forecast ocean product with ECMWF HRES or ENS forecast winds. For the initial real-data test, ERA5 is the appropriate, well-validated choice.

### Variables

| CDS API variable name | NetCDF variable | CF standard_name | Units | OpenBerg target |
|---|---|---|---|---|
| `10m_u_component_of_wind` | `u10` | `eastward_wind` | m s⁻¹ | `x_wind` ✅ |
| `10m_v_component_of_wind` | `v10` | `northward_wind` | m s⁻¹ | `y_wind` ✅ |
| `significant_height_of_combined_wind_waves_and_swell` | `swh` | `significant_height_of_combined_wind_waves_and_swell` | m | `sea_surface_wave_significant_height` (optional) |
| `mean_wave_direction` | `mwd` | `sea_surface_wave_from_direction` | degrees | `sea_surface_wave_from_direction` (optional) |

### Variable Mapping — How standard_names connect to OpenBerg

```
u10 (standard_name: 'eastward_wind')
     └──> xy2eastnorth_mapping in basereader: 'eastward_wind' -> 'x_wind'   ✅

v10 (standard_name: 'northward_wind')
     └──> xy2eastnorth_mapping in basereader: 'northward_wind' -> 'y_wind'  ✅
```

Also accepted via variable_aliases:
```
'x_wind_10m' -> 'x_wind'   (if standard_name is 'x_wind_10m')
'y_wind_10m' -> 'y_wind'
```

### Coordinates

| Role | Name | standard_name | Units | Notes |
|---|---|---|---|---|
| Time | `time` | `time` | `hours since 1900-01-01 00:00:00.0` | See caveat below |
| Latitude | `latitude` | `latitude` | `degrees_north` | 1D regular |
| Longitude | `longitude` | `longitude` | `degrees_east` | -180 to 180 with `area` bbox |

> ⚠️ **Known caveat:** Recent CDS API downloads may produce a `valid_time` dimension instead of `time`. The CF reader looks for `time` or `vtime`. If detection fails:
> ```python
> import xarray as xr
> ds = xr.open_dataset('era5.nc').rename({'valid_time': 'time'})
> from opendrift.readers.reader_netCDF_CF_generic import Reader
> wind_reader = Reader(ds)
> ```

### Specifications

| Property | Value |
|---|---|
| **Horizontal resolution** | **0.25° × 0.25°** (~30 km) |
| **Temporal resolution** | **Hourly** |
| **Vertical levels** | Surface only (10 m above ground) — no depth dimension |
| **Grid type** | Regular lat-lon |
| **Temporal coverage** | **1940-01-01 to present** (~5 day latency) |
| **Spatial coverage** | Global |
| **Nature** | Reanalysis |
| **NetCDF output** | ✅ Yes — specified via `'format': 'netcdf'` in CDS API request |

### OpenDrift Reader Compatibility

| Reader | Status | Notes |
|---|---|---|
| `reader_netCDF_CF_generic` | ✅ **Direct** | No extra packages needed after download |
| `reader_copernicusmarine` | ❌ N/A | ERA5 is from CDS, not CMEMS |
| `standard_name_mapping` needed? | ❌ **Normally none** | `u10` → `eastward_wind` auto-maps to `x_wind` |

### Suitability

✅ **Ideal for validation / historical experiments** paired with GLORYS12.  
✅ Hourly resolution is finer than GLORYS12's daily ocean data — OpenDrift handles the mismatch by linear interpolation.  
⚠️ For fully operational forecast mode, replace ERA5 with ECMWF forecast winds in future work.

---

## Full Compatibility Matrix: OpenBerg ↔ All Datasets

| OpenBerg variable | Fallback | GLORYS12 (Mode 1) | ANFC (Mode 2) | ERA5 (Wind) | Status |
|---|---|---|---|---|---|
| `x_sea_water_velocity` | **NONE** | `uo` ✅ | `uo` ✅ | — | Covered both modes |
| `y_sea_water_velocity` | **NONE** | `vo` ✅ | `vo` ✅ | — | Covered both modes |
| `x_wind` | **NONE** | — | — | `u10` ✅ | ERA5 both modes |
| `y_wind` | **NONE** | — | — | `v10` ✅ | ERA5 both modes |
| `land_binary_mask` | **NONE** | — | — | — | LandmaskReader ✅ |
| `sea_floor_depth_below_sea_level` | 10000 | `deptho` aliased | `deptho` aliased | — | Covered |
| `sea_surface_height` | 0 | `zos` aliased | `zos` aliased | — | Covered |
| `sea_water_temperature` | 2°C | `thetao` aliased | `thetao` aliased | — | Covered |
| `sea_water_salinity` | 35 PSU | `so` direct | `so` direct | — | Covered |
| `sea_ice_area_fraction` | 0 | `siconc` ✅ | `siconc` ✅ | — | Covered |
| `sea_ice_thickness` | 0 | `sithick` ✅ | `sithick` ✅ | — | Covered |
| `sea_ice_x_velocity` | 0 | `usi` aliased | `usi` aliased | — | Covered |
| `sea_ice_y_velocity` | 0 | `vsi` aliased | `vsi` aliased | — | Covered |
| `sea_surface_wave_significant_height` | 0 | — | — | `swh` (optional) | Optional |

---

## Minimal Dataset Subset for First Real 48-Hour Experiment

### Design Principles for First Test
- **Intentionally small** — only what is needed, nothing extra
- **Surface currents only** (`depth = 0 to 1 m`) for Mode 1 test
- **Tight bounding box** around the existing seed point (lon=0°, lat=72°)
- **Short time window** — exactly 3 days (Jan 1–3, 2024) for a 48-h simulation + 1 day buffer
- **Minimum variables** — only `uo`, `vo` for ocean; `u10`, `v10` for wind
- **Mode 1 (GLORYS12) first** — reanalysis for regression testing; switch to forecast (Mode 2) after validation

### Recommended Bounding Box

```
Seed point    : lon=0.0°, lat=72.0° (Greenland Sea, matches test_run.py)
Bounding box  : lon=-10° to +10°, lat=68° to 76°  (tight 20°×8° region)
Rationale     : 5 icebergs drifting with 0.1 m/s current for 48h move ~17 km max
                This 20°×8° box provides 10° margin on each side
```

### GLORYS12 Minimal Subset Parameters (Mode 1 First Test)

```
dataset_id    : cmems_mod_glo_phy_my_0.083deg_P1D-m
variables     : uo, vo  (uo only = eastward current, vo = northward current)
start_datetime: 2024-01-01T00:00:00
end_datetime  : 2024-01-03T00:00:00  (3 days = 2 daily timesteps + endpoints)
min_longitude : -10.0
max_longitude : +10.0
min_latitude  :  68.0
max_latitude  :  76.0
min_depth     :   0.0
max_depth     :   1.0   (top level only, ~0.494 m)

Estimated file size: ~1–3 MB (2 daily timesteps × 2 variables × small region × 1 depth level)
```

### ERA5 Minimal Subset Parameters (Both Modes)

```
dataset       : reanalysis-era5-single-levels
product_type  : reanalysis
variables     : 10m_u_component_of_wind, 10m_v_component_of_wind
year          : 2024
month         : 01
days          : 01, 02, 03  (48h simulation + 1 day buffer)
hours         : all 24 hours each day (hourly)
area          : [76, -10, 68, 10]  (North, West, South, East)
format        : netcdf

Estimated file size: ~1–2 MB (72 hourly steps × 2 variables × small region)
```

### Reader Stack for First Test

```python
from opendrift.readers.reader_netCDF_CF_generic import Reader
from opendrift.readers.reader_global_landmask import Reader as LandmaskReader

ocean_reader = Reader('data/glorys12_test.nc')    # auto-detects uo→x_sea_water_velocity
wind_reader  = Reader('data/era5_wind_test.nc')   # auto-detects u10→x_wind
land_reader  = LandmaskReader()

o.add_reader([ocean_reader, wind_reader, land_reader])
```

### Pre-Flight Gates Before Simulation

```
[ ] Both files downloaded into data/ subdirectory
[ ] xr.open_dataset() on each file — confirms it opens
[ ] inspect_netcdf() from real_data_plan.py run on each file
[ ] 'eastward_sea_water_velocity' confirmed present in ocean file
[ ] 'eastward_wind' confirmed present in wind file
[ ] time dimensions both named 'time' (not 'valid_time')
[ ] Reader(ocean_file) prints detected variables including x_sea_water_velocity
[ ] Reader(wind_file) prints detected variables including x_wind
[ ] 6-hour test run (not 48h) with real data completes without fallback warnings
```

---

## Mode Decision Tree

```
Q: Is the simulation date in the past (>2 years ago)?
   YES → MODE 1 (GLORYS12): cmems_mod_glo_phy_my_0.083deg_P1D-m
   NO  → Q: Is the date within the last ~2 years or in the future?
         YES → MODE 2 (ANFC): cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m
               (covers recent past + 10-day forecast)
```

Both modes use the same ERA5 wind for historical/validation.  
For true real-time operational forecasting, ECMWF NWP forecast winds will eventually replace ERA5.

---

## Files Not Yet Ready

```
[ ] data/glorys12_test.nc   — not downloaded (pending CMEMS account + copernicusmarine install)
[ ] data/era5_wind_test.nc  — not downloaded (pending CDS API key + cdsapi install)
```

**The model is NOT yet ready for real-data prediction.**

---

*Sources: CMEMS product pages (verified 2026-09-26), ECMWF/CDS ERA5 documentation, OpenDrift 1.14.11 source (`basereader/__init__.py` lines 56–105, `reader_copernicusmarine.py`).*

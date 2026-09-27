"""
dataset_config.py
=================
Configuration constants for two OpenBerg operational modes.

MODE 1 — HISTORICAL / VALIDATION
  Ocean  : GLORYS12V1 (GLOBAL_MULTIYEAR_PHY_001_030)
  Purpose: Hindcast, validation, comparison with observed positions
  Use when: simulation date is in the past (>~2 years ago)

MODE 2 — OPERATIONAL FORECAST
  Ocean  : GLO12 Analysis/Forecast (GLOBAL_ANALYSISFORECAST_PHY_001_024)
  Purpose: Future iceberg trajectory prediction
  Use when: simulation date is recent (<~2 years) or in the future

Both modes:
  Wind   : ERA5 hourly single levels (reanalysis)
  Future : replace ERA5 with ECMWF NWP forecast for full real-time operation

This file contains ONLY configuration — no simulation is run here.
No credentials, passwords, or API keys are stored here.

Sources verified:
  - https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030/description
  - https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description
  - https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
  - OpenDrift 1.14.11 basereader/__init__.py (variable_aliases, xy2eastnorth_mapping)
  - OpenDrift 1.14.11 reader_copernicusmarine.py
"""


# =============================================================================
# SHARED CONSTANTS
# =============================================================================

# Target simulation parameters for first real-data 48-hour test
# (Greenland Sea — matches existing test_run.py seed point)
FIRST_TEST = {
    "seed_lon":       0.0,
    "seed_lat":      72.0,
    "start_datetime": "2024-01-01T00:00:00",
    "end_datetime":   "2024-01-03T00:00:00",   # 48 h after start + 1 day buffer

    # Bounding box: tight 20°×8° window around seed, giving ~10° margin
    "min_lon": -10.0,
    "max_lon": +10.0,
    "min_lat":  68.0,
    "max_lat":  76.0,

    # Iceberg seed parameters (from test_run.py)
    "n_particles": 5,
    "length": 100,   # m
    "draft":   90,   # m
    "sail":    10,   # m
    "width":   30,   # m
}


# =============================================================================
# MODE 1 — HISTORICAL OCEAN DATASET (GLORYS12V1)
# =============================================================================

HISTORICAL_OCEAN_DATASET = {
    # Identity
    "mode":              "historical_validation",
    "product_id":        "GLOBAL_MULTIYEAR_PHY_001_030",
    "dataset_id":        "cmems_mod_glo_phy_my_0.083deg_P1D-m",
    "model":             "GLORYS12V1",
    "nature":            "reanalysis",
    "product_url":       "https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030/description",

    # Temporal specification
    "temporal_coverage_start": "1993-01-01",
    "temporal_coverage_end":   "present",   # ~1 week latency
    "temporal_resolution":     "P1D",       # daily means

    # Spatial specification
    "horizontal_resolution_deg": 1.0 / 12.0,   # ~8 km
    "spatial_coverage":          "global",
    "vertical_levels":           50,
    "depth_range_m":             (0.494, 5727.917),
    "depth_positive":            "down",         # CF convention in file

    # Variable inventory: netcdf_name -> (CF standard_name, units, dims, openberg_target)
    "variables": {
        "uo":      ("eastward_sea_water_velocity",        "m s-1",     "4D", "x_sea_water_velocity"),
        "vo":      ("northward_sea_water_velocity",       "m s-1",     "4D", "y_sea_water_velocity"),
        "thetao":  ("sea_water_potential_temperature",    "degrees_C", "4D", "sea_water_temperature"),
        "so":      ("sea_water_salinity",                 "PSU",       "4D", "sea_water_salinity"),
        "zos":     ("sea_surface_height_above_geoid",     "m",         "3D", "sea_surface_height"),
        "siconc":  ("sea_ice_area_fraction",              "1",         "3D", "sea_ice_area_fraction"),
        "sithick": ("sea_ice_thickness",                  "m",         "3D", "sea_ice_thickness"),
        "usi":     ("eastward_sea_ice_velocity",          "m s-1",     "3D", "sea_ice_x_velocity"),
        "vsi":     ("northward_sea_ice_velocity",         "m s-1",     "3D", "sea_ice_y_velocity"),
        "deptho":  ("sea_floor_depth_below_geoid",        "m",         "2D", "sea_floor_depth_below_sea_level"),
    },

    # Coordinate names as they appear in the NetCDF file
    "coords": {
        "time":      {"name": "time",      "units": "hours since 1950-01-01 00:00:00"},
        "latitude":  {"name": "latitude",  "standard_name": "latitude",  "units": "degrees_north"},
        "longitude": {"name": "longitude", "standard_name": "longitude", "units": "degrees_east"},
        "depth":     {"name": "depth",     "standard_name": "depth",     "units": "m",
                      "positive": "down"},
    },

    # reader_netCDF_CF_generic mapping
    # NOT needed: all variables carry correct CF standard_name attributes
    # Auto-alias chain used internally:
    #   eastward_sea_water_velocity  -> x_sea_water_velocity
    #   northward_sea_water_velocity -> y_sea_water_velocity
    #   sea_water_potential_temperature -> sea_water_temperature
    #   sea_surface_height_above_geoid  -> sea_surface_height
    #   sea_floor_depth_below_geoid     -> sea_floor_depth_below_sea_level
    #   eastward_sea_ice_velocity       -> sea_ice_x_velocity
    #   northward_sea_ice_velocity      -> sea_ice_y_velocity
    "standard_name_mapping": {},

    # Minimal download for first 48-h test (surface currents only)
    "first_test_download": {
        "dataset_id":   "cmems_mod_glo_phy_my_0.083deg_P1D-m",
        "variables":    ["uo", "vo"],
        "start_datetime": FIRST_TEST["start_datetime"],
        "end_datetime":   FIRST_TEST["end_datetime"],
        "minimum_longitude": FIRST_TEST["min_lon"],
        "maximum_longitude": FIRST_TEST["max_lon"],
        "minimum_latitude":  FIRST_TEST["min_lat"],
        "maximum_latitude":  FIRST_TEST["max_lat"],
        "minimum_depth":  0.0,
        "maximum_depth":  1.0,    # top level only: ~0.494 m
        "output_filename": "data/glorys12_test.nc",
        "estimated_size_mb": "1-3",
    },
}


# =============================================================================
# MODE 2 — OPERATIONAL FORECAST OCEAN DATASET (GLO12 ANFC)
# =============================================================================

FORECAST_OCEAN_DATASET = {
    # Identity
    "mode":       "operational_forecast",
    "product_id": "GLOBAL_ANALYSISFORECAST_PHY_001_024",

    # IMPORTANT — dataset_id selection:
    # Use the '-cur-' dataset for 3D uo/vo (mandatory for OpenBerg)
    # The dataset WITHOUT '-cur-' contains only 2D fields (SSH, SST, ice) — NOT suitable
    "dataset_id_daily_3D":   "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",   # 3D daily (RECOMMENDED)
    "dataset_id_6hourly_3D": "cmems_mod_glo_phy-cur_anfc_0.083deg_PT6H-i",  # 6-hourly 3D
    "dataset_id_hourly_sfc": "cmems_mod_glo_phy_anfc_merged-uv_PT1H-i",     # 1-hourly surface SMOC

    # For OpenBerg's first real-forecast test, use the daily 3D dataset
    "recommended_dataset_id": "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",

    "model":        "GLO12 (Mercator Ocean International operational system)",
    "nature":       "analysis + 10-day forecast, updated daily",
    "product_url":  "https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description",

    # Temporal specification
    "temporal_coverage_start": "~2 years ago (rolling window)",
    "temporal_coverage_end":   "today + 10 days (forecast horizon)",
    "temporal_resolution":     "P1D",   # daily means for 3D currents

    # Spatial specification (identical to GLORYS12)
    "horizontal_resolution_deg": 1.0 / 12.0,
    "spatial_coverage":          "global",
    "vertical_levels":           50,
    "depth_range_m":             (0.494, 5727.917),
    "depth_positive":            "down",

    # Variables (identical names and standard_names to GLORYS12)
    "variables": {
        "uo":      ("eastward_sea_water_velocity",        "m s-1",     "4D", "x_sea_water_velocity"),
        "vo":      ("northward_sea_water_velocity",       "m s-1",     "4D", "y_sea_water_velocity"),
        "thetao":  ("sea_water_potential_temperature",    "degrees_C", "4D", "sea_water_temperature"),
        "so":      ("sea_water_salinity",                 "PSU",       "4D", "sea_water_salinity"),
        "zos":     ("sea_surface_height_above_geoid",     "m",         "3D", "sea_surface_height"),
        "siconc":  ("sea_ice_area_fraction",              "1",         "3D", "sea_ice_area_fraction"),
        "sithick": ("sea_ice_thickness",                  "m",         "3D", "sea_ice_thickness"),
        "usi":     ("eastward_sea_ice_velocity",          "m s-1",     "3D", "sea_ice_x_velocity"),
        "vsi":     ("northward_sea_ice_velocity",         "m s-1",     "3D", "sea_ice_y_velocity"),
    },

    # Coordinate names — identical to GLORYS12
    "coords": {
        "time":      {"name": "time",      "units": "hours since 1950-01-01 00:00:00"},
        "latitude":  {"name": "latitude",  "standard_name": "latitude",  "units": "degrees_north"},
        "longitude": {"name": "longitude", "standard_name": "longitude", "units": "degrees_east"},
        "depth":     {"name": "depth",     "standard_name": "depth",     "units": "m",
                      "positive": "down"},
    },

    "standard_name_mapping": {},   # none needed — identical CF attributes to GLORYS12

    # Minimal download for first 48-h forecast test
    "first_test_download": {
        "dataset_id":   "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
        "variables":    ["uo", "vo"],
        "start_datetime": FIRST_TEST["start_datetime"],   # use a recent date within ~2 yr window
        "end_datetime":   FIRST_TEST["end_datetime"],
        "minimum_longitude": FIRST_TEST["min_lon"],
        "maximum_longitude": FIRST_TEST["max_lon"],
        "minimum_latitude":  FIRST_TEST["min_lat"],
        "maximum_latitude":  FIRST_TEST["max_lat"],
        "minimum_depth":  0.0,
        "maximum_depth":  1.0,
        "output_filename": "data/anfc_test.nc",
        "estimated_size_mb": "1-3",
    },

    # Known gotcha: do NOT use the dataset without '-cur-' for 3D currents
    "known_issues": [
        "cmems_mod_glo_phy_anfc_0.083deg_P1D-m (no '-cur-') = 2D fields only (SSH, SST, sea ice)",
        "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m (with '-cur-') = 3D uo/vo — USE THIS ONE",
        "The hourly SMOC dataset (PT1H-i) includes tidal/wave contributions in the surface current",
        "Sliding window: data older than ~2 years is not available in this product",
    ],
}


# =============================================================================
# ERA5 WIND DATASET (used by BOTH modes)
# =============================================================================

ERA5_WIND_DATASET = {
    # Identity
    "cds_dataset_id": "reanalysis-era5-single-levels",
    "product_type":   "reanalysis",
    "nature":         "reanalysis",
    "product_url":    "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels",
    "api_setup_url":  "https://cds.climate.copernicus.eu/how-to-api",

    # Temporal
    "temporal_coverage_start": "1940-01-01",
    "temporal_coverage_end":   "present",   # ~5 day latency
    "temporal_resolution":     "PT1H",      # hourly

    # Spatial
    "horizontal_resolution_deg": 0.25,     # ~30 km globally
    "spatial_coverage":          "global",
    "vertical_levels":           1,        # surface only (10 m AGL)
    "no_depth_dimension":        True,     # 3D array: (time, latitude, longitude)

    # Variables: netcdf_name -> (CDS API name, CF standard_name, units, openberg_target)
    "variables": {
        "u10": (
            "10m_u_component_of_wind",
            "eastward_wind",
            "m s-1",
            "x_wind",
        ),
        "v10": (
            "10m_v_component_of_wind",
            "northward_wind",
            "m s-1",
            "y_wind",
        ),
        # Optional wave variables (improve wave radiation force in OpenBerg):
        "swh": (
            "significant_height_of_combined_wind_waves_and_swell",
            "significant_height_of_combined_wind_waves_and_swell",
            "m",
            "sea_surface_wave_significant_height",
        ),
        "mwd": (
            "mean_wave_direction",
            "sea_surface_wave_from_direction",
            "degrees",
            "sea_surface_wave_from_direction",
        ),
    },

    # Coordinate names as they appear in downloaded NetCDF
    "coords": {
        "time":      {"name": "time",      "units": "hours since 1900-01-01 00:00:00.0"},
        "latitude":  {"name": "latitude",  "standard_name": "latitude",  "units": "degrees_north"},
        "longitude": {"name": "longitude", "standard_name": "longitude", "units": "degrees_east"},
    },

    # standard_name mapping
    # NOT needed for standard CDS downloads — u10/v10 carry correct CF attributes
    # u10 standard_name='eastward_wind'  -> xy2eastnorth_mapping -> x_wind  ✅
    # v10 standard_name='northward_wind' -> xy2eastnorth_mapping -> y_wind  ✅
    "standard_name_mapping": {},

    # Known issues
    "known_issues": [
        "Recent CDS downloads may name time dim 'valid_time' instead of 'time'",
        "Fix: xr.open_dataset('era5.nc').rename({'valid_time': 'time'}), then pass ds to Reader()",
        "Longitude range: use 'area' parameter in request to get -180..+180 (not 0..360)",
        "ERA5 is reanalysis only — does NOT provide future forecasts",
    ],

    # Minimal download for first 48-h test (only required variables)
    "first_test_download": {
        "dataset":      "reanalysis-era5-single-levels",
        "product_type": "reanalysis",
        "variable": [
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
        ],
        "year":  "2024",
        "month": "01",
        "day":   ["01", "02", "03"],              # 3 days = 48h + 1 day buffer
        "time":  [f"{h:02d}:00" for h in range(24)],  # all 24 hours per day = 72 steps
        # area: [North, West, South, East]
        "area": [
            FIRST_TEST["max_lat"],
            FIRST_TEST["min_lon"],
            FIRST_TEST["min_lat"],
            FIRST_TEST["max_lon"],
        ],
        "format": "netcdf",
        "output_filename": "data/era5_wind_test.nc",
        "estimated_size_mb": "1-2",
    },
}


# =============================================================================
# MODE SELECTION HELPER
# =============================================================================

def select_ocean_dataset(simulation_date_str):
    """
    Return the appropriate ocean dataset config for a given simulation date.
    Does NOT download anything — returns config dict only.

    Args:
        simulation_date_str: ISO date string, e.g. '2024-01-01'

    Returns:
        dict: either HISTORICAL_OCEAN_DATASET or FORECAST_OCEAN_DATASET
    """
    from datetime import datetime, timedelta, timezone
    sim_date = datetime.fromisoformat(simulation_date_str.replace('T', ' ')[:10])
    cutoff   = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=730)   # ~2 years ago

    if sim_date < cutoff:
        print(f"[select_ocean_dataset] {simulation_date_str} is >2 years ago -> MODE 1: GLORYS12")
        return HISTORICAL_OCEAN_DATASET
    else:
        print(f"[select_ocean_dataset] {simulation_date_str} is recent/future -> MODE 2: ANFC forecast")
        return FORECAST_OCEAN_DATASET


# =============================================================================
# ACCESS NOTES (NO CREDENTIALS STORED HERE)
# =============================================================================
#
# CMEMS (both ocean datasets):
#   1. Register at: https://marine.copernicus.eu/register-overview
#   2. Install:     venv\Scripts\pip install copernicusmarine
#   3. Authenticate (one time):
#      Store in ~/.netrc:
#        machine copernicusmarine
#        login   <your_username>
#        password <your_password>
#      OR set environment variables:
#        COPERNICUSMARINE_SERVICE_USERNAME=<your_username>
#        COPERNICUSMARINE_SERVICE_PASSWORD=<your_password>
#
# CDS / ERA5:
#   1. Register at: https://cds.climate.copernicus.eu/user/register
#   2. Install:     venv\Scripts\pip install cdsapi
#   3. Configure:   create ~/.cdsapirc with content:
#        url: https://cds.climate.copernicus.eu/api
#        key: <your-api-key>
#      (API key found at: https://cds.climate.copernicus.eu/how-to-api)
#
# IMPORTANT: Do NOT commit ~/.netrc or ~/.cdsapirc to version control.
# =============================================================================


if __name__ == "__main__":
    from datetime import datetime

    print("=" * 65)
    print("dataset_config.py — OpenBerg Two-Mode Dataset Configuration")
    print("=" * 65)

    print("\n--- MODE 1: HISTORICAL / VALIDATION ---")
    print(f"  Product  : {HISTORICAL_OCEAN_DATASET['product_id']}")
    print(f"  Dataset  : {HISTORICAL_OCEAN_DATASET['dataset_id']}")
    print(f"  Coverage : {HISTORICAL_OCEAN_DATASET['temporal_coverage_start']} to {HISTORICAL_OCEAN_DATASET['temporal_coverage_end']}")
    print(f"  Res.     : {HISTORICAL_OCEAN_DATASET['horizontal_resolution_deg']:.4f}° × daily, {HISTORICAL_OCEAN_DATASET['vertical_levels']} depth levels")
    print(f"  Variables: {list(HISTORICAL_OCEAN_DATASET['variables'].keys())}")

    print("\n--- MODE 2: OPERATIONAL FORECAST ---")
    print(f"  Product  : {FORECAST_OCEAN_DATASET['product_id']}")
    print(f"  Dataset  : {FORECAST_OCEAN_DATASET['recommended_dataset_id']}")
    print(f"  Coverage : {FORECAST_OCEAN_DATASET['temporal_coverage_start']} to {FORECAST_OCEAN_DATASET['temporal_coverage_end']}")
    print(f"  Res.     : {FORECAST_OCEAN_DATASET['horizontal_resolution_deg']:.4f}° × daily, {FORECAST_OCEAN_DATASET['vertical_levels']} depth levels")
    print(f"  Variables: {list(FORECAST_OCEAN_DATASET['variables'].keys())}")

    print("\n--- ERA5 WIND (both modes) ---")
    print(f"  Dataset  : {ERA5_WIND_DATASET['cds_dataset_id']}")
    print(f"  Coverage : {ERA5_WIND_DATASET['temporal_coverage_start']} to {ERA5_WIND_DATASET['temporal_coverage_end']}")
    print(f"  Res.     : {ERA5_WIND_DATASET['horizontal_resolution_deg']}° × hourly, surface only")
    print(f"  Variables: {list(ERA5_WIND_DATASET['variables'].keys())}")

    print("\n--- FIRST TEST PARAMETERS ---")
    print(f"  Seed     : lon={FIRST_TEST['seed_lon']}, lat={FIRST_TEST['seed_lat']}")
    print(f"  Window   : {FIRST_TEST['start_datetime']} to {FIRST_TEST['end_datetime']}")
    print(f"  BBox     : lon {FIRST_TEST['min_lon']} to {FIRST_TEST['max_lon']}, "
          f"lat {FIRST_TEST['min_lat']} to {FIRST_TEST['max_lat']}")
    print(f"  Ocean    : ~{HISTORICAL_OCEAN_DATASET['first_test_download']['estimated_size_mb']} MB")
    print(f"  Wind     : ~{ERA5_WIND_DATASET['first_test_download']['estimated_size_mb']} MB")

    print("\n--- MODE SELECTION DEMO ---")
    select_ocean_dataset("2020-06-01")   # old date → MODE 1
    select_ocean_dataset("2025-01-01")   # recent → MODE 2

    print("\nStatus: Config only — no data downloaded.")

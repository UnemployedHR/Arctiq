"""
=============================================================================
real_data_plan.py  --  OpenBerg Real-Data Contract Document
=============================================================================
PURPOSE
-------
This file documents the EXACT data contract that a real ocean-current NetCDF
and real wind NetCDF must satisfy before they can be passed into OpenBerg.

This file does NOT run a simulation.
It is a reference document and a checklist / validation scaffold.

The working constant-forcing test is preserved in test_run.py (DO NOT EDIT).

Verified environment:
  OpenDrift   : 1.14.11
  OpenBerg    : opendrift.models.openberg.OpenBerg
  Python      : venv/Scripts/python.exe

Source of truth: opendrift/models/openberg.py  (lines 297-321, 427-621)
                 opendrift/readers/basereader/__init__.py (lines 56-105)
=============================================================================


=============================================================================
SECTION 1 - ALL OPENBERG REQUIRED_VARIABLES
=============================================================================

Extracted verbatim from OpenBerg.required_variables dict (openberg.py:297-321)

Variable name                           | fallback  | profiles | important
------------------------------------------------------------------------- ----
x_sea_water_velocity                    | NONE      | YES      | YES (MUST)
y_sea_water_velocity                    | NONE      | YES      | YES (MUST)
x_wind                                  | NONE      | -        | YES (MUST)
y_wind                                  | NONE      | -        | YES (MUST)
land_binary_mask                        | NONE      | -        | YES (MUST)
sea_floor_depth_below_sea_level         | 10000     | -        | default-ok
sea_surface_height                      | 0         | -        | NOT important
sea_surface_x_slope                     | 0         | -        | NOT important
sea_surface_y_slope                     | 0         | -        | NOT important
horizontal_diffusivity                  | 100       | -        | NOT important
sea_surface_wave_significant_height     | 0         | -        | default-ok
sea_surface_wave_from_direction         | 0         | -        | default-ok
sea_surface_wave_stokes_drift_x_velocity| 0         | -        | NOT important
sea_surface_wave_stokes_drift_y_velocity| 0         | -        | NOT important
sea_water_temperature                   | 2 (degC)  | YES      | NOT important
sea_water_salinity                      | 35 (PSU)  | YES      | NOT important
sea_ice_area_fraction                   | 0         | -        | NOT important
sea_ice_thickness                       | 0         | -        | NOT important
sea_ice_x_velocity                      | 0         | -        | NOT important
sea_ice_y_velocity                      | 0         | -        | NOT important

KEY:
  fallback=NONE  -> simulation WILL CRASH if not provided by a reader
  profiles=YES   -> the variable is needed at multiple depth levels (z-profiles)
  important=YES  -> OpenDrift will log WARNING if missing; default=ok for others


=============================================================================
SECTION 2 - OCEAN CURRENT VARIABLES (must come from ocean NetCDF)
=============================================================================

MANDATORY - simulation cannot run without these:

  x_sea_water_velocity   [m/s]   Eastward  sea water velocity
  y_sea_water_velocity   [m/s]   Northward sea water velocity

IMPORTANT NOTES:
  - Both have fallback=None -> CRASH if missing from ALL readers
  - Both have profiles=True -> depth-level data strongly preferred
    (used by depth-integrated mode when drift:vertical_profile=True)
  - Surface-only (2D) data is accepted when vertical_profile=False (default)
  - The model depth-integrates from surface to iceberg draft when
    drift:vertical_profile=True is set via o.set_config()

CF standard_name accepted by reader_netCDF_CF_generic (auto-detected):
  PRIMARY    : 'eastward_sea_water_velocity'  / 'northward_sea_water_velocity'
  ALIASES    : 'sea_water_x_velocity'         / 'sea_water_y_velocity'
               'baroclinic_x_sea_water_velocity' / 'baroclinic_y_...'
               'eastward_current_velocity'    / 'northward_current_velocity'
               'eastward_tidal_current'       / 'northward_tidal_current'
               'eastward_geostrophic_current_velocity'  / northward...
               ... (full list: basereader/__init__.py lines 86-99)

OPTIONAL ocean variables (have numeric fallbacks, but improve realism):
  sea_floor_depth_below_sea_level  [m]     fallback=10000  (grounding check)
  sea_surface_height               [m]     fallback=0      (grounding check)
  sea_surface_x_slope              [m/m]   fallback=0      (sea slope force)
  sea_surface_y_slope              [m/m]   fallback=0      (sea slope force)
  sea_water_temperature            [degC]  fallback=2      (melting calc)
  sea_water_salinity               [PSU]   fallback=35     (melting calc)
  sea_ice_area_fraction            [0-1]   fallback=0      (ice interaction)
  sea_ice_thickness                [m]     fallback=0      (ice interaction)
  sea_ice_x_velocity               [m/s]  fallback=0      (ice drag force)
  sea_ice_y_velocity               [m/s]  fallback=0      (ice drag force)


=============================================================================
SECTION 3 - WIND VARIABLES (must come from wind/atmosphere NetCDF)
=============================================================================

MANDATORY - simulation cannot run without these:

  x_wind   [m/s]   Eastward  wind speed at 10m
  y_wind   [m/s]   Northward wind speed at 10m

IMPORTANT NOTES:
  - Both have fallback=None -> CRASH if missing from ALL readers
  - Wind affects: air drag force on sail, wave radiation force (indirect),
    wave erosion melting (when melting enabled)

CF standard_name accepted by reader_netCDF_CF_generic:
  PRIMARY    : 'eastward_wind'   / 'northward_wind'
  ALIASES    : 'x_wind_10m'     / 'y_wind_10m'    (auto-aliased)
  NOTE: ECMWF model has special handling for multi-level winds (10m selected)

OPTIONAL wave variables (have fallbacks of 0, but improve drift accuracy):
  sea_surface_wave_significant_height      [m]        fallback=0
  sea_surface_wave_from_direction          [degrees]  fallback=0
  sea_surface_wave_stokes_drift_x_velocity [m/s]      fallback=0
  sea_surface_wave_stokes_drift_y_velocity [m/s]      fallback=0


=============================================================================
SECTION 4 - MELTING / ICE INTERACTION - ADDITIONAL REQUIREMENTS
=============================================================================

By default: o processes:melting = False  (melting is DISABLED at init)

If you ENABLE melting via:
    o.set_config('processes:melting', True)

Then the following variables become ACTIVELY USED (not just fallback):

  For wave melting (melting:wave, default True when melting enabled):
    - x_wind, y_wind              (already required above)
    - sea_water_temperature       (surface layer T, from T_profile[0])
    - sea_ice_area_fraction       (wave erosion suppressed in ice)

  For lateral melting (melting:lateral, default True):
    - sea_water_temperature       (PROFILE - all depth levels to draft)
    - sea_water_salinity          (PROFILE - all depth levels to draft)

  For basal melting (melting:basal, default True):
    - sea_water_temperature       (at depth of iceberg base - basal layer)
    - sea_water_salinity          (at depth of iceberg base - basal layer)
    - x_sea_water_velocity        (basal layer)
    - y_sea_water_velocity        (basal layer)

  CONCLUSION: If melting is enabled, you NEED full depth profiles of:
    - sea_water_temperature   (multiple depth levels, m/degC)
    - sea_water_salinity      (multiple depth levels, PSU)
    - x_sea_water_velocity    (multiple depth levels, m/s)
    - y_sea_water_velocity    (multiple depth levels, m/s)

  These must be provided as 4D arrays: (time, depth, lat, lon)

Roll-over process (always enabled by default):
  Uses: sea_water_temperature, sea_water_salinity  (surface values only)
  These reshape iceberg dimensions when stability criterion fails.


=============================================================================
SECTION 5 - UNITS REFERENCE TABLE (COMPLETE)
=============================================================================

Variable                                  | Unit        | Notes
---------------------------------------------------------- ----------------
x_sea_water_velocity                      | m/s         | +East
y_sea_water_velocity                      | m/s         | +North
x_wind                                    | m/s         | +East, at 10m
y_wind                                    | m/s         | +North, at 10m
sea_floor_depth_below_sea_level           | m           | positive downward
sea_surface_height                        | m           | above mean sea level
sea_surface_x_slope                       | dimensionless (m/m)
sea_surface_y_slope                       | dimensionless (m/m)
sea_surface_wave_significant_height       | m
sea_surface_wave_from_direction           | degrees     | oceanographic conv.
sea_surface_wave_stokes_drift_x_velocity  | m/s
sea_surface_wave_stokes_drift_y_velocity  | m/s
sea_water_temperature                     | degC        | Celsius
sea_water_salinity                        | PSU (psu)   | practical salinity
sea_ice_area_fraction                     | 0-1         | fraction
sea_ice_thickness                         | m
sea_ice_x_velocity                        | m/s
sea_ice_y_velocity                        | m/s
land_binary_mask                          | 0 or 1      | 1=land (auto from LandmaskReader)

Iceberg element properties (set at seed time):
  length  | m   | horizontal length
  width   | m   | horizontal width
  sail    | m   | height above waterline
  draft   | m   | depth below waterline
  (mass computed internally: width*(sail+draft)*length*rho_iceb*weight_coef)


=============================================================================
SECTION 6 - COORDINATE AND DIMENSION REQUIREMENTS FOR NETCDF FILES
=============================================================================

The reader_netCDF_CF_generic auto-detects coordinates by:
  1. standard_name attribute on coordinate variables
  2. axis attribute (X, Y, Z, T)
  3. Variable names: 'longitude','lon', 'latitude','lat', 'time','depth'
  4. CoordinateAxisType attribute

Required dimensions (minimum for 2D surface-only data):
  - time   : 1D array of times with CF-compliant units
              e.g. "hours since 1900-01-01 00:00:00.0 UTC"
  - lat    : 1D or 2D array with standard_name='latitude'   units='degrees_north'
  - lon    : 1D or 2D array with standard_name='longitude'  units='degrees_east'

For 3D data (surface + depth levels for profiles):
  - depth  : 1D array with standard_name='depth' or axis='Z'
              Sign convention: positive UP (standard CF) or positive DOWN
              If 'positive' attribute is absent, reader assumes positive UP
              Reader will negate to get negative-downward internally.

Variable shape (3D data with depth):
  data_variable : (time, depth, lat, lon)  -- most common for structured grids

Projection:
  - Lat/lon grids (most common):  proj4 = '+proj=latlong'  (auto-detected)
  - Regular spacing required (max 5% deviation in delta_x, delta_y)
  - Longitudes >360 are automatically corrected by reader

Grid coverage required:
  - Must cover ALL seed positions + expected drift area
  - Must cover simulation time window COMPLETELY
  - Reader will use fallback values outside its coverage
  - Multiple readers can be stacked: o.add_reader([ocean_reader, wind_reader])


=============================================================================
SECTION 7 - TIME DIMENSION REQUIREMENTS
=============================================================================

  - Time variable must have CF-compliant units attribute
    Format: "<unit> since <reference_date>"
    Examples:
      "hours since 1900-01-01 00:00:00.0 UTC"
      "seconds since 1970-01-01 00:00:00"
      "days since 1950-01-01"

  - calendar attribute is optional but recommended:
    "standard", "gregorian", "proleptic_gregorian"

  - Time coverage must span the full simulation:
    start_time  <= seed time
    end_time    >= seed time + simulation duration

  - Temporal resolution: reader interpolates linearly between time steps.
    Finer resolution = better accuracy. Typical:
      Ocean currents : 1-6 hour steps (CMEMS products)
      Wind           : 1-3 hour steps (ERA5, ECMWF)

  - If multiple files: use glob pattern with reader_netCDF_CF_generic:
    Reader("my_ocean_*.nc")   -- files are concatenated along time


=============================================================================
SECTION 8 - SPATIAL COVERAGE REQUIREMENTS
=============================================================================

  - Ocean reader must cover: seed position + full expected drift envelope
  - Wind reader must cover the same region
  - Both readers should ideally cover the same domain
  - If a reader does not cover a particle position, fallback values are used

  Typical spatial resolution:
    CMEMS GLORYS12 (ocean): 1/12° (~8 km)
    ERA5 (wind):            0.25° (~28 km)
    TOPAZ4 (Arctic ocean):  12 km

  For the Norwegian/Greenland Sea scenario (current test):
    Min recommended coverage:
      lon: -20°E to +20°E
      lat:  60°N to  80°N


=============================================================================
SECTION 9 - HOW reader_netCDF_CF_generic DETECTS VARIABLES
=============================================================================

The reader detects variables ONLY if:
  1. The NetCDF variable has a 'standard_name' attribute  (preferred), OR
  2. The user provides a standard_name_mapping dict to Reader()

Detection logic (reader_netCDF_CF_generic.py:345-378):
  - Reads all variables with ndim >= 2
  - Checks var.attrs['standard_name']
  - Applies variable_aliases mapping (basereader/__init__.py:56-83)
  - Applies xy2eastnorth_mapping for east/north -> x/y conversion

CRITICAL: Without 'standard_name', variables are SKIPPED automatically.

To use a NetCDF file whose variables lack standard_name:
    from opendrift.readers.reader_netCDF_CF_generic import Reader
    r = Reader('ocean.nc', standard_name_mapping={
        'uo': 'eastward_sea_water_velocity',
        'vo': 'northward_sea_water_velocity',
    })

Accepted CF standard_names that map to OpenBerg variables:

  OpenBerg variable              | Accepted CF standard_name(s)
  ---------------------------------------------------------------
  x_sea_water_velocity  <- eastward_sea_water_velocity
                           sea_water_x_velocity
                           baroclinic_eastward_sea_water_velocity
                           eastward_current_velocity
                           eastward_geostrophic_current_velocity
  y_sea_water_velocity  <- northward_sea_water_velocity
                           sea_water_y_velocity
                           baroclinic_northward_sea_water_velocity
                           northward_current_velocity
                           northward_geostrophic_current_velocity
  x_wind                <- eastward_wind
                           x_wind_10m  (alias)
  y_wind                <- northward_wind
                           y_wind_10m  (alias)
  sea_surface_height    <- sea_surface_elevation
                           sea_surface_elevation_anomaly
                           sea_surface_height_above_mean_sea_level
                           sea_surface_height_above_sea_level
                           sea_surface_height_above_geoid
  sea_floor_depth_below_sea_level <- sea_floor_depth_below_sea_surface
                                     sea_floor_depth_below_geoid
  sea_water_temperature <- sea_water_potential_temperature (alias)
  sea_ice_x_velocity    <- x_sea_ice_velocity  (alias)
                           eastward_sea_ice_velocity
  sea_ice_y_velocity    <- y_sea_ice_velocity  (alias)
                           northward_sea_ice_velocity


=============================================================================
SECTION 10 - PLANNED REAL-DATA ARCHITECTURE
=============================================================================

Final pipeline (not yet implemented - pending data verification):

    Ocean NetCDF (e.g. CMEMS GLORYS12 or TOPAZ4)
         |
         |  Variables with standard_name:
         |    eastward_sea_water_velocity  -> x_sea_water_velocity  [m/s]
         |    northward_sea_water_velocity -> y_sea_water_velocity  [m/s]
         |    sea_water_potential_temperature -> sea_water_temperature [degC]
         |    sea_water_salinity           -> sea_water_salinity    [PSU]
         |    sea_floor_depth_below_sea_level                       [m]
         |    sea_surface_height_above_sea_level -> sea_surface_height [m]
         v
    reader_netCDF_CF_generic(ocean_file.nc)
         |
         +-----> x_sea_water_velocity
         +-----> y_sea_water_velocity
         +-----> sea_water_temperature   (profiles if 3D)
         +-----> sea_water_salinity      (profiles if 3D)
         +-----> sea_floor_depth_below_sea_level
         +-----> sea_surface_height

    Wind NetCDF (e.g. ERA5 or ECMWF)
         |
         |  Variables with standard_name:
         |    eastward_wind   -> x_wind  [m/s]
         |    northward_wind  -> y_wind  [m/s]
         |    (Optional) significant_height_of_combined_wind_waves_and_swell
         |               -> sea_surface_wave_significant_height [m]
         v
    reader_netCDF_CF_generic(wind_file.nc)
         |
         +-----> x_wind
         +-----> y_wind
         +-----> sea_surface_wave_significant_height (optional)

    Land mask (always required):
    reader_global_landmask()
         +-----> land_binary_mask

    STACK ORDER (most specific first):
    o.add_reader([ocean_reader, wind_reader, landmask_reader])

         |
         v
    OpenBerg.run()
         |
         v
    iceberg_trajectory.nc    (NetCDF, CF-compliant trajectory output)
    iceberg_trajectory.csv   (machine-readable lat/lon/time)
    iceberg_trajectory_plot.png


=============================================================================
SECTION 11 - PRE-FLIGHT CHECKLIST (run BEFORE using real NetCDF)
=============================================================================

Before using any real NetCDF file, verify the following:

OCEAN FILE:
  [ ] File opens without error: xr.open_dataset('ocean.nc')
  [ ] 'eastward_sea_water_velocity' OR 'uo' (with mapping) present
  [ ] 'northward_sea_water_velocity' OR 'vo' present
  [ ] Spatial coverage includes the seed region + drift envelope
  [ ] Time range covers: seed_time to seed_time + duration
  [ ] Time units are CF-compliant (e.g. "hours since YYYY-MM-DD")
  [ ] Longitude values are in expected range (not >360 or mixing conventions)
  [ ] Grid spacing is regular (constant delta_lon, delta_lat)
  [ ] Depth coordinate is present (for profiles / melting)
  [ ] standard_name attributes present on all data variables

WIND FILE:
  [ ] File opens without error
  [ ] 'eastward_wind' OR 'x_wind_10m' present
  [ ] 'northward_wind' OR 'y_wind_10m' present
  [ ] Spatial and temporal coverage same requirements as ocean file
  [ ] standard_name attributes present

BOTH FILES:
  [ ] Time zones consistent (all UTC)
  [ ] Fill values / NaNs handled (NetCDF _FillValue attribute set correctly)
  [ ] Variables inspected with ncdump or xarray before loading into OpenDrift

READER INSTANTIATION TEST (before full run):
    from opendrift.readers.reader_netCDF_CF_generic import Reader
    r = Reader('ocean.nc')
    print(r)  # shows detected variables, time range, spatial coverage


=============================================================================
SECTION 12 - WHAT IS NOT YET IMPLEMENTED
=============================================================================

  [ ] Real ocean NetCDF reader (pending data download and verification)
  [ ] Real wind NetCDF reader  (pending data download and verification)
  [ ] Full depth-profile integration (drift:vertical_profile=True)
  [ ] Melting enabled (processes:melting=True)
  [ ] Animation output
  [ ] Multi-iceberg ensemble with varied dimensions
  [ ] Comparison against observed positions

NOT claiming the model is ready for real prediction until:
  1. A real ocean NetCDF file passes the pre-flight checklist above
  2. reader_netCDF_CF_generic successfully detects x_sea_water_velocity
     and y_sea_water_velocity from it
  3. A short (6-hour) test simulation runs WITHOUT reverting to fallback
     values for the two mandatory ocean variables
  4. The same verification is done for wind variables

=============================================================================
END OF DATA CONTRACT DOCUMENT
=============================================================================
"""

# ---------------------------------------------------------------------------
# VALIDATION SCAFFOLD  (to be used later when real NetCDF files are available)
# ---------------------------------------------------------------------------
# Uncomment and adapt each section when testing a real file.

OCEAN_NC_FILE = None   # e.g. 'data/glorys12_20240101.nc'
WIND_NC_FILE  = None   # e.g. 'data/era5_20240101.nc'

REQUIRED_OCEAN_VARS_CF = [
    'eastward_sea_water_velocity',   # -> x_sea_water_velocity (MANDATORY)
    'northward_sea_water_velocity',  # -> y_sea_water_velocity (MANDATORY)
]

OPTIONAL_OCEAN_VARS_CF = [
    'sea_water_potential_temperature',   # -> sea_water_temperature
    'sea_water_salinity',
    'sea_floor_depth_below_sea_level',
    'sea_surface_height_above_sea_level',
]

REQUIRED_WIND_VARS_CF = [
    'eastward_wind',    # -> x_wind (MANDATORY)
    'northward_wind',   # -> y_wind (MANDATORY)
]

OPTIONAL_WAVE_VARS_CF = [
    'significant_height_of_combined_wind_waves_and_swell',
    'eastward_surface_stokes_drift',
    'northward_surface_stokes_drift',
]


def inspect_netcdf(filepath, label='File'):
    """
    Inspect a NetCDF file and print its variables, dimensions, time range
    and spatial coverage. Run this BEFORE passing it to OpenDrift.
    Does NOT run a simulation.
    """
    try:
        import xarray as xr
        import numpy as np
    except ImportError:
        print("xarray not available")
        return

    print(f"\n{'='*60}")
    print(f"INSPECTING: {label}")
    print(f"  Path: {filepath}")
    print(f"{'='*60}")

    ds = xr.open_dataset(filepath, decode_times=True)

    print(f"\nDimensions:")
    for dim, size in ds.dims.items():
        print(f"  {dim}: {size}")

    print(f"\nVariables ({len(ds.data_vars)}):")
    for var in ds.data_vars:
        v = ds[var]
        sn = v.attrs.get('standard_name', 'NO STANDARD_NAME  <-- PROBLEM')
        units = v.attrs.get('units', 'no units')
        print(f"  {var:40s} shape={str(v.shape):20s} std={sn}  [{units}]")

    # Check time
    if 'time' in ds:
        try:
            t = ds['time'].values
            print(f"\nTime range:")
            print(f"  Start : {t[0]}")
            print(f"  End   : {t[-1]}")
            print(f"  Steps : {len(t)}")
        except Exception as e:
            print(f"  Time parse error: {e}")

    # Check spatial
    for cname in ['lon', 'longitude', 'nav_lon']:
        if cname in ds:
            lon = ds[cname].values.flatten()
            print(f"\nLongitude ({cname}): {lon.min():.2f} to {lon.max():.2f}")
            break
    for cname in ['lat', 'latitude', 'nav_lat']:
        if cname in ds:
            lat = ds[cname].values.flatten()
            print(f"Latitude  ({cname}): {lat.min():.2f} to {lat.max():.2f}")
            break

    # Check depth
    for cname in ['depth', 'lev', 'z', 'depthu', 'depthv', 'deptht']:
        if cname in ds:
            depth = ds[cname].values
            print(f"\nDepth ({cname}): {depth.min():.1f} to {depth.max():.1f} m  ({len(depth)} levels)")
            break

    ds.close()
    print(f"\n{'='*60}\n")


def check_required_standard_names(filepath, required_names, label=''):
    """
    Verify that a NetCDF file contains variables with the required CF
    standard_name attributes. Reports missing ones clearly.
    """
    try:
        import xarray as xr
    except ImportError:
        return

    ds = xr.open_dataset(filepath)
    found = {v.attrs.get('standard_name', ''): name
             for name, v in ds.data_vars.items()}

    print(f"\nChecking required standard_names in {label or filepath}:")
    all_ok = True
    for sn in required_names:
        if sn in found:
            print(f"  [OK]      {sn}  (variable: {found[sn]})")
        else:
            print(f"  [MISSING] {sn}  <-- REQUIRED: simulation will crash")
            all_ok = False

    ds.close()
    return all_ok


# ---------------------------------------------------------------------------
# EXAMPLE USAGE (uncomment when files are available):
# ---------------------------------------------------------------------------
#
# inspect_netcdf(OCEAN_NC_FILE, 'Ocean current file')
# inspect_netcdf(WIND_NC_FILE,  'Wind file')
#
# ocean_ok = check_required_standard_names(
#     OCEAN_NC_FILE, REQUIRED_OCEAN_VARS_CF, 'Ocean file')
# wind_ok = check_required_standard_names(
#     WIND_NC_FILE, REQUIRED_WIND_VARS_CF, 'Wind file')
#
# if ocean_ok and wind_ok:
#     print("\nBOTH files pass pre-flight check. Proceeding to simulation.")
# else:
#     print("\nPre-flight FAILED. Fix missing variables before running OpenBerg.")
#
# ---------------------------------------------------------------------------
# END OF FILE
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print(__doc__)
    print("\nThis file is a data contract document.")
    print("Set OCEAN_NC_FILE and WIND_NC_FILE, then uncomment the")
    print("'EXAMPLE USAGE' section at the bottom to inspect real files.")

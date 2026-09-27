import os
import sys
import numpy as np
from datetime import datetime, timedelta
from opendrift.models.openberg import OpenBerg
from opendrift.readers import reader_netCDF_CF_generic

print("==================================================")
print(" OPENBERG INTEGRATION TEST (OCEAN + WIND)")
print("==================================================")

# 1. Paths and setup
copernicus_file = r'data\copernicus\glorys_iceberg_20857\iceberg_20857_glorys_uo_vo_20210601_20210810.nc'
era5_wind_file = r'data\wind\iceberg_20857\era5_iceberg_20857_wind_20210601_20210810.nc'
out_dir = r'data\results\iceberg_20857'
os.makedirs(out_dir, exist_ok=True)

out_nc = os.path.join(out_dir, 'real_run_24h.nc')
out_csv = os.path.join(out_dir, 'real_run_24h.csv')
out_png = os.path.join(out_dir, 'real_run_24h.png')

# 2. Setup readers
print(f"Loading ocean reader from: {copernicus_file}")
ocean_reader = reader_netCDF_CF_generic.Reader(copernicus_file)

print(f"Loading wind reader from: {era5_wind_file}")
wind_reader = reader_netCDF_CF_generic.Reader(
    era5_wind_file,
    standard_name_mapping={'u10': 'x_wind', 'v10': 'y_wind'}
)

print(f"\nOcean reader exposes variables: {ocean_reader.variables}")
print(f"Wind reader exposes variables: {wind_reader.variables}")

if 'x_sea_water_velocity' not in ocean_reader.variables or 'y_sea_water_velocity' not in ocean_reader.variables:
    print("ERROR: Required ocean velocity variables not found in the reader!")
    sys.exit(1)
if 'x_wind' not in wind_reader.variables or 'y_wind' not in wind_reader.variables:
    print("ERROR: Required wind velocity variables not found in the reader!")
    sys.exit(1)

# 3. Create model instance and add readers
print("\nInitializing OpenBerg model...")
o = OpenBerg(loglevel=20)
o.add_reader(ocean_reader)
o.add_reader(wind_reader)

print("Configuring: drift:vertical_profile = False")
o.set_config('drift:vertical_profile', False)

# 4. Verify seed time is within reader range
seed_time = datetime(2021, 6, 2, 16, 41, 0)
print(f"\nOcean reader time range: {ocean_reader.start_time} to {ocean_reader.end_time}")
print(f"Wind reader time range: {wind_reader.start_time} to {wind_reader.end_time}")
print(f"Seed time: {seed_time}")

if not (ocean_reader.start_time <= seed_time <= ocean_reader.end_time):
    print("ERROR: Seed time is outside the ocean reader's time range.")
    sys.exit(1)
if not (wind_reader.start_time <= seed_time <= wind_reader.end_time):
    print("ERROR: Seed time is outside the wind reader's time range.")
    sys.exit(1)

# 5. Seed the iceberg
assumed_length = 100
assumed_width = 30
assumed_draft = 90
assumed_sail = 10

seed_lon = -62.41
seed_lat = 59.42667

print(f"\nSeeding iceberg 20857 at lon={seed_lon}, lat={seed_lat}")
print(f"ASSUMED Geometry: length={assumed_length}m, width={assumed_width}m, draft={assumed_draft}m, sail={assumed_sail}m")

o.seed_elements(
    lon=seed_lon,
    lat=seed_lat,
    time=seed_time,
    length=assumed_length,
    width=assumed_width,
    draft=assumed_draft,
    sail=assumed_sail
)

# 6. Run 24-hour test
print("\nRunning 24-hour ocean+wind integration test...")
try:
    o.run(
        duration=timedelta(hours=24),
        time_step=timedelta(hours=1),
        time_step_output=timedelta(hours=1),
        outfile=out_nc,
        export_variables=['lon', 'lat', 'time', 'moving', 'status']
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\nSimulation failed with error:\n{e}")
    sys.exit(1)

# 7. Output exports
print("\nExporting results...")
import pandas as pd
lon_arr = np.array(o.result.lon)
lat_arr = np.array(o.result.lat)
times = np.array(o.result.time)
rows = []
for p_idx in range(lon_arr.shape[0]):
    for t_idx, t in enumerate(times):
        lo = lon_arr[p_idx, t_idx]
        la = lat_arr[p_idx, t_idx]
        if np.isfinite(lo) and np.isfinite(la):
            rows.append({
                'time': str(t),
                'particle': p_idx + 1,
                'lon': float(lo),
                'lat': float(la)
            })
pd.DataFrame(rows).to_csv(out_csv, index=False)
o.plot(filename=out_png, fast=True)

# 8. Verification output
print("\n==================================================")
print(" TEST COMPLETE")
print("==================================================")
print(f"Number of time steps calculated: {o.steps_calculated}")

if len(lon_arr) > 0 and len(lon_arr[0]) > 0:
    initial_lon = lon_arr[0, 0]
    initial_lat = lat_arr[0, 0]
    active_mask = ~np.isnan(lon_arr[0])
    final_lon = lon_arr[0, active_mask][-1]
    final_lat = lat_arr[0, active_mask][-1]
    print(f"Initial position: lon={initial_lon:.5f}, lat={initial_lat:.5f}")
    print(f"Final position:   lon={final_lon:.5f}, lat={final_lat:.5f}")

print("\nSUCCESS: 24-hour integration test finished.")

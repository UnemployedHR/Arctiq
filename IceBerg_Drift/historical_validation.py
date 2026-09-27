import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from opendrift.models.openberg import OpenBerg
from opendrift.readers import reader_netCDF_CF_generic

# Haversine distance formula (returns km)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

print("==================================================")
print(" HISTORICAL TRAJECTORY VALIDATION - ICEBERG 20857")
print("==================================================")

# 1. Setup paths
copernicus_file = r'data\copernicus\glorys_iceberg_20857\iceberg_20857_glorys_uo_vo_20210601_20210810.nc'
era5_wind_file = r'data\wind\iceberg_20857\era5_iceberg_20857_wind_20210601_20210810.nc'
iip_file = r'data\iip\IIP_2021IcebergSeason.csv'
out_dir = r'data\results\iceberg_20857'
os.makedirs(out_dir, exist_ok=True)

out_nc = os.path.join(out_dir, 'historical_validation_20857.nc')
out_csv = os.path.join(out_dir, 'historical_validation_20857.csv')
val_csv = os.path.join(out_dir, 'validation_20857_comparison.csv')
out_png = os.path.join(out_dir, 'validation_20857_trajectory.png')
out_txt = os.path.join(out_dir, 'validation_20857_summary.txt')

# 2. Verify files exist
for f in [copernicus_file, era5_wind_file, iip_file]:
    if not os.path.exists(f):
        sys.exit(f"ERROR: File not found: {f}")

# 3. Load IIP data
df = pd.read_csv(iip_file)
# Note: Ensure the filter matches integer or string appropriately. Iceberg number is usually int.
df = df[df['ICEBERG_NUMBER'].astype(str) == '20857'].copy()

# Fix parsing of date and time
df["DATETIME"] = pd.to_datetime(
    df["SIGHTING_DATE"].astype(str) + " " +
    df["SIGHTING_TIME"].astype(str)
)

df = df.sort_values('DATETIME').reset_index(drop=True)

# Missing values check
if df[['DATETIME', 'SIGHTING_LATITUDE', 'SIGHTING_LONGITUDE']].isnull().values.any():
    sys.exit("ERROR: Missing values found in DATETIME, SIGHTING_LATITUDE, or SIGHTING_LONGITUDE.")

# Check count
if len(df) != 21:
    sys.exit(f"ERROR: Expected 21 observations, but found {len(df)}")

start_time = df['DATETIME'].iloc[0]
end_time = df['DATETIME'].iloc[-1]
start_lon = df['SIGHTING_LONGITUDE'].iloc[0]
start_lat = df['SIGHTING_LATITUDE'].iloc[0]
duration = end_time - start_time

print(f"IIP Observations: {len(df)}")
print(f"First: {start_time}, lat={start_lat:.5f}, lon={start_lon:.5f}")
print(f"Last:  {end_time}, lat={df['SIGHTING_LATITUDE'].iloc[-1]:.5f}, lon={df['SIGHTING_LONGITUDE'].iloc[-1]:.5f}")
print(f"Duration: {duration}")

# 4. Initialize Readers
print("\nLoading generic CF readers...")
ocean_reader = reader_netCDF_CF_generic.Reader(copernicus_file)
wind_reader = reader_netCDF_CF_generic.Reader(
    era5_wind_file,
    standard_name_mapping={'u10': 'x_wind', 'v10': 'y_wind'}
)

if 'x_sea_water_velocity' not in ocean_reader.variables:
    sys.exit("ERROR: x_sea_water_velocity missing in ocean reader.")
if 'x_wind' not in wind_reader.variables:
    sys.exit("ERROR: x_wind missing in wind reader.")

if ocean_reader.start_time > start_time or ocean_reader.end_time < end_time:
    print("WARNING: Ocean data may not fully cover simulation period.")
if wind_reader.start_time > start_time or wind_reader.end_time < end_time:
    print("WARNING: Wind data may not fully cover simulation period.")

# 5. Model Setup
print("\nConfiguring OpenBerg...")
o = OpenBerg(loglevel=20)
o.add_reader(ocean_reader)
o.add_reader(wind_reader)
o.set_config('drift:vertical_profile', False)

assumed_length = 100
assumed_width = 30
assumed_draft = 90
assumed_sail = 10

o.seed_elements(
    lon=start_lon,
    lat=start_lat,
    time=start_time,
    length=assumed_length,
    width=assumed_width,
    draft=assumed_draft,
    sail=assumed_sail
)

# 6. Run Simulation
print("\nRunning full historical validation simulation...")
try:
    o.run(
        duration=duration,
        time_step=timedelta(hours=1),
        time_step_output=timedelta(hours=1),
        outfile=out_nc,
        export_variables=['lon', 'lat', 'time', 'moving', 'status']
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(f"Simulation failed: {e}")

# 7. Post-processing
lon_arr = np.array(o.result.lon)
lat_arr = np.array(o.result.lat)
times = np.array(o.result.time)
n_steps = len(times)

# Export raw trajectory CSV
rows = []
for t_idx, t in enumerate(times):
    lo = lon_arr[0, t_idx]
    la = lat_arr[0, t_idx]
    if np.isfinite(lo) and np.isfinite(la):
        rows.append({'time': str(t), 'lon': float(lo), 'lat': float(la)})
pd.DataFrame(rows).to_csv(out_csv, index=False)

# Interpolate and Validation
# Ensure all times are converted to UNIX epoch seconds for safe interpolation
model_times_sec = np.array([pd.to_datetime(t).timestamp() for t in times])
model_lons = lon_arr[0, :]
model_lats = lat_arr[0, :]

val_rows = []
errors = []

print("\nValidating and computing metrics...")
for idx, row in df.iterrows():
    obs_time_sec = row['DATETIME'].timestamp()
    
    # Allow 1-hour tolerance for interpolation boundaries (3600 seconds)
    if obs_time_sec >= (model_times_sec[0] - 3600) and obs_time_sec <= (model_times_sec[-1] + 3600):
        
        # Valid model indices
        valid_mask = np.isfinite(model_lons) & np.isfinite(model_lats)
        
        if valid_mask.sum() > 1:
            interp_lon = np.interp(obs_time_sec, model_times_sec[valid_mask], model_lons[valid_mask])
            interp_lat = np.interp(obs_time_sec, model_times_sec[valid_mask], model_lats[valid_mask])
            
            err_km = haversine(row['SIGHTING_LATITUDE'], row['SIGHTING_LONGITUDE'], interp_lat, interp_lon)
            errors.append(err_km)
            val_rows.append({
                'timestamp': row['DATETIME'],
                'observed_lat': row['SIGHTING_LATITUDE'],
                'observed_lon': row['SIGHTING_LONGITUDE'],
                'modeled_lat': interp_lat,
                'modeled_lon': interp_lon,
                'error_km': err_km
            })

val_df = pd.DataFrame(val_rows)
val_df.to_csv(val_csv, index=False)

if len(errors) > 0:
    mean_err = np.mean(errors)
    median_err = np.median(errors)
    rmse = np.sqrt(np.mean(np.square(errors)))
    max_err = np.max(errors)
    min_err = np.min(errors)
else:
    mean_err = median_err = rmse = max_err = min_err = np.nan

# 8. Report
summary = f"""
==================================================
VALIDATION SUMMARY - ICEBERG 20857
==================================================
Simulation Status: Success
Simulation Period: {start_time} to {end_time}
Model Time Steps: {n_steps}
IIP Observations: {len(df)}
Successfully Matched: {len(errors)} ({(len(errors)/len(df))*100:.1f}%)

Metrics (km):
- Mean Error:   {mean_err:.2f}
- Median Error: {median_err:.2f}
- RMSE:         {rmse:.2f}
- Max Error:    {max_err:.2f}
- Min Error:    {min_err:.2f}

Positions:
Start Observed: lon={start_lon:.5f}, lat={start_lat:.5f}
Start Modeled:  lon={val_df['modeled_lon'].iloc[0]:.5f}, lat={val_df['modeled_lat'].iloc[0]:.5f}

End Observed:   lon={df['SIGHTING_LONGITUDE'].iloc[-1]:.5f}, lat={df['SIGHTING_LATITUDE'].iloc[-1]:.5f}
End Modeled:    lon={val_df['modeled_lon'].iloc[-1]:.5f}, lat={val_df['modeled_lat'].iloc[-1]:.5f}

Output Locations:
- {out_nc}
- {out_csv}
- {val_csv}
- {out_png}
- {out_txt}
"""

with open(out_txt, 'w') as f:
    f.write(summary)
print(summary)

# 9. Plotting
plt.figure(figsize=(10, 8))
plt.plot(df['SIGHTING_LONGITUDE'], df['SIGHTING_LATITUDE'], 'o--', label='IIP Observed', markersize=6, color='black')
plt.plot(model_lons, model_lats, '-', label='OpenBerg Modeled', linewidth=2, color='blue')
plt.plot(start_lon, start_lat, 'g*', markersize=14, label='Start Point')
plt.plot(df['SIGHTING_LONGITUDE'].iloc[-1], df['SIGHTING_LATITUDE'].iloc[-1], 'rX', markersize=12, label='End Point Observed')
plt.xlabel('Longitude (degrees East)')
plt.ylabel('Latitude (degrees North)')
plt.title('Iceberg 20857 Trajectory Validation (GLORYS + ERA5)\\nBaseline without parameter optimization')
plt.legend()
plt.grid(True)
plt.savefig(out_png, dpi=150, bbox_inches='tight')
plt.close()

print("Validation completed successfully.")

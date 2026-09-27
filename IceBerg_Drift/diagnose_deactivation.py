import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("==================================================")
print(" DIAGNOSTIC ANALYSIS: EARLY DEACTIVATION ")
print("==================================================")

# 1. Load the model netcdf
model_nc_path = r'data\results\iceberg_20857\historical_validation_20857.nc'
ds_model = xr.open_dataset(model_nc_path)

status = ds_model.status.values[0, :]
active_mask = (status == 0)

last_active_idx = np.where(active_mask)[0][-1]
first_deact_idx = last_active_idx + 1 if last_active_idx + 1 < len(status) else last_active_idx

print(f"Final active step index: {last_active_idx}")
print(f"Status at final active step: {status[last_active_idx]}")
if first_deact_idx != last_active_idx:
    print(f"Status at deactivation step: {status[first_deact_idx]}")

flag_meanings = ds_model.status.attrs.get('flag_meanings', 'unknown')
flag_values = ds_model.status.attrs.get('flag_values', 'unknown')
print(f"\nStatus flag meanings: {flag_meanings}")
print(f"Status flag values: {flag_values}")

last_lon = ds_model.lon.values[0, last_active_idx]
last_lat = ds_model.lat.values[0, last_active_idx]
last_time = ds_model.time.values[last_active_idx]

print(f"\nFinal Active Position:")
print(f"Time: {last_time}")
print(f"Lon: {last_lon:.5f}")
print(f"Lat: {last_lat:.5f}")

# 2. Check Environmental Datasets
glorys_path = r'data\copernicus\glorys_iceberg_20857\iceberg_20857_glorys_uo_vo_20210601_20210810.nc'
ds_glorys = xr.open_dataset(glorys_path)
glorys_lon_min, glorys_lon_max = float(ds_glorys.longitude.min()), float(ds_glorys.longitude.max())
glorys_lat_min, glorys_lat_max = float(ds_glorys.latitude.min()), float(ds_glorys.latitude.max())

era5_path = r'data\wind\iceberg_20857\era5_iceberg_20857_wind_20210601_20210810.nc'
ds_era5 = xr.open_dataset(era5_path)
era5_lon_min, era5_lon_max = float(ds_era5.longitude.min()), float(ds_era5.longitude.max())
era5_lat_min, era5_lat_max = float(ds_era5.latitude.min()), float(ds_era5.latitude.max())

print(f"\nEnvironmental Domains:")
print(f"GLORYS: lon [{glorys_lon_min:.5f}, {glorys_lon_max:.5f}], lat [{glorys_lat_min:.5f}, {glorys_lat_max:.5f}]")
print(f"ERA5:   lon [{era5_lon_min:.5f}, {era5_lon_max:.5f}], lat [{era5_lat_min:.5f}, {era5_lat_max:.5f}]")

outside_glorys = not (glorys_lon_min <= last_lon <= glorys_lon_max and glorys_lat_min <= last_lat <= glorys_lat_max)
outside_era5 = not (era5_lon_min <= last_lon <= era5_lon_max and era5_lat_min <= last_lat <= era5_lat_max)

print("\nAssessment:")
print(f"Outside GLORYS bounds: {outside_glorys}")
print(f"Outside ERA5 bounds:   {outside_era5}")

# 3. Final 10 valid records from CSV
csv_path = r'data\results\iceberg_20857\historical_validation_20857.csv'
df_traj = pd.read_csv(csv_path)
print("\nFinal 10 active records from trajectory CSV:")
print(df_traj.tail(10))

# 4. Plot Diagnostic Map
iip_file = r'data\iip\IIP_2021IcebergSeason.csv'
df_iip = pd.read_csv(iip_file)
df_iip = df_iip[df_iip['ICEBERG_NUMBER'].astype(str) == '20857'].copy()

plt.figure(figsize=(10, 8))
plt.plot(df_iip['SIGHTING_LONGITUDE'], df_iip['SIGHTING_LATITUDE'], 'o--', label='IIP Observations', color='black')
plt.plot(df_traj['lon'], df_traj['lat'], '-', label='Model Trajectory', color='blue', linewidth=2)
plt.plot(last_lon, last_lat, 'rX', markersize=14, label='Deactivation Point')

plt.plot([glorys_lon_min, glorys_lon_max, glorys_lon_max, glorys_lon_min, glorys_lon_min],
         [glorys_lat_min, glorys_lat_min, glorys_lat_max, glorys_lat_max, glorys_lat_min],
         'g--', label='GLORYS Boundary')

plt.plot([era5_lon_min, era5_lon_max, era5_lon_max, era5_lon_min, era5_lon_min],
         [era5_lat_min, era5_lat_min, era5_lat_max, era5_lat_max, era5_lat_min],
         'm:', label='ERA5 Boundary')

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Diagnostic Map: Deactivation Analysis')
plt.legend()
plt.grid(True)
plt.savefig(r'data\results\iceberg_20857\deactivation_diagnostic.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nDiagnostic map saved to: data/results/iceberg_20857/deactivation_diagnostic.png")

import os
import xarray as xr
import sys

file_path = r'data\wind\iceberg_20857\era5_iceberg_20857_wind_20210601_20210810.nc'

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    sys.exit(1)

size_bytes = os.path.getsize(file_path)
print(f"File Size: {size_bytes / (1024*1024):.2f} MB ({size_bytes} bytes)")

try:
    ds = xr.open_dataset(file_path)
    
    print("\n--- DIMENSIONS ---")
    for dim, size in ds.sizes.items():
        print(f"{dim}: {size}")
    
    print("\n--- COORDINATES ---")
    print(list(ds.coords.keys()))
    
    if 'latitude' in ds.coords:
        print(f"Latitude range: {ds.latitude.min().item():.5f} to {ds.latitude.max().item():.5f}")
    if 'longitude' in ds.coords:
        print(f"Longitude range: {ds.longitude.min().item():.5f} to {ds.longitude.max().item():.5f}")
        
    if 'time' in ds.coords:
        time_vals = ds.time.values
        print(f"Time range: {time_vals.min()} to {time_vals.max()}")
        print(f"Number of time steps: {len(time_vals)}")
        
    print("\n--- VARIABLES ---")
    for var_name in ds.data_vars:
        var = ds[var_name]
        print(f"\nVariable: {var_name}")
        print(f"  Standard Name: {var.attrs.get('standard_name', 'None')}")
        print(f"  Long Name: {var.attrs.get('long_name', 'None')}")
        print(f"  Units: {var.attrs.get('units', 'None')}")
        fill_val = var.encoding.get('_FillValue', var.attrs.get('_FillValue', 'None'))
        print(f"  _FillValue: {fill_val}")
        print(f"  missing_value: {var.attrs.get('missing_value', 'None')}")
        
    ds.close()
    
except Exception as e:
    print(f"Error reading NetCDF: {e}")

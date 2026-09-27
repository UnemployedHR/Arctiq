import os
import xarray as xr
import sys

file_path = r'data\copernicus\glorys_iceberg_20857\iceberg_20857_glorys_uo_vo_20210601_20210810.nc'

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    sys.exit(1)

size_bytes = os.path.getsize(file_path)
print(f"File Size: {size_bytes / (1024*1024):.2f} MB ({size_bytes} bytes)")

try:
    ds = xr.open_dataset(file_path)
    
    print("\n--- DIMENSIONS ---")
    for dim, size in ds.dims.items():
        print(f"{dim}: {size}")
    
    print("\n--- COORDINATES ---")
    print(list(ds.coords.keys()))
    
    if 'latitude' in ds.coords:
        print(f"Latitude range: {ds.latitude.min().item():.5f} to {ds.latitude.max().item():.5f}")
        print(f"Latitude units: {ds.latitude.attrs.get('units', 'None')}")
    
    if 'longitude' in ds.coords:
        print(f"Longitude range: {ds.longitude.min().item():.5f} to {ds.longitude.max().item():.5f}")
        print(f"Longitude units: {ds.longitude.attrs.get('units', 'None')}")
        
    if 'time' in ds.coords:
        time_vals = ds.time.values
        print(f"Time range: {time_vals.min()} to {time_vals.max()}")
        print(f"Number of time steps: {len(time_vals)}")
        if len(time_vals) > 1:
            diff = (time_vals[1] - time_vals[0]).astype('timedelta64[h]')
            print(f"Time step interval: {diff}")
            
    if 'depth' in ds.coords:
        depth_vals = ds.depth.values
        print(f"Depth/Elevation values: {depth_vals}")
        print(f"Depth units: {ds.depth.attrs.get('units', 'None')}")
        
    print("\n--- VARIABLES ---")
    print(list(ds.data_vars))
    
    for var_name in ['uo', 'vo']:
        if var_name in ds:
            var = ds[var_name]
            print(f"\nVariable: {var_name}")
            print(f"  Shape: {var.shape}")
            print(f"  Units: {var.attrs.get('units', 'None')}")
            fill_val = var.encoding.get('_FillValue', var.attrs.get('_FillValue', 'None'))
            print(f"  _FillValue: {fill_val}")
            print(f"  missing_value: {var.attrs.get('missing_value', 'None')}")
        
    ds.close()
    
except Exception as e:
    print(f"Error reading NetCDF: {e}")

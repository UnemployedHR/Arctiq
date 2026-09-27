import pandas as pd
import xarray as xr
import numpy as np
from opendrift.models.openberg import OpenBerg
from opendrift.readers import reader_global_landmask

# Phase 2: IIP SIZE and SHAPE
df_iip = pd.read_csv('data/iip/IIP_2021IcebergSeason.csv')
df_iip = df_iip[df_iip['ICEBERG_NUMBER'].astype(str) == '20857']
print("IIP SIZE:", df_iip['SIZE'].unique())
print("IIP SHAPE:", df_iip['SHAPE'].unique())

# Phase 1 & 4: Trajectory and Coastline interaction
nc_path = 'data/results/iceberg_20857/historical_validation_20857.nc'
ds = xr.open_dataset(nc_path)

lons = ds.lon.values[0]
lats = ds.lat.values[0]
times = ds.time.values
status = ds.status.values[0]

df_traj = pd.DataFrame({'time': times, 'lon': lons, 'lat': lats, 'status': status})
idx_stranded = np.where(status == 1)[0]
if len(idx_stranded) > 0:
    first_strand_idx = idx_stranded[0]
    print(f"\nFirst strand index: {first_strand_idx}")
    start_idx = max(0, first_strand_idx - 20)
    end_idx = min(len(status), first_strand_idx + 2)
    print("\nLAST STEPS:")
    print(df_traj.iloc[start_idx:end_idx].to_string())
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0 # Earth radius in km
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c
    
    print("\nStep distances (km):")
    for i in range(start_idx+1, first_strand_idx+1):
        dist = haversine(df_traj['lat'].iloc[i-1], df_traj['lon'].iloc[i-1], df_traj['lat'].iloc[i], df_traj['lon'].iloc[i])
        print(f"Step {i-1} to {i}: {dist:.2f} km")
        
    last_lon = df_traj['lon'].iloc[first_strand_idx]
    last_lat = df_traj['lat'].iloc[first_strand_idx]
    
    # Let's try to query the landmask
    reader_landmask = reader_global_landmask.Reader()
    print(f"\nEvaluating distance to coast at ({last_lon:.5f}, {last_lat:.5f})")
    
    # Evaluate landmask at the final position
    # The reader typically returns land_binary_mask (0=ocean, 1=land)
    env = reader_landmask.get_variables(['land_binary_mask'], 
                                        time=pd.to_datetime('2021-06-19 12:41:00'), 
                                        lon=[last_lon], 
                                        lat=[last_lat])
    print(f"land_binary_mask exactly at point: {env['land_binary_mask']}")
    
else:
    print("No stranded status found.")

# Phase 3: OpenBerg Geometry
o = OpenBerg(loglevel=50)
print("\nDefault IcebergObj geometry:")
# Just creating a generic element to see defaults
o.seed_elements(lon=0, lat=0, time=pd.to_datetime('2021-06-01'))
el = o.elements
print(f"length: {el.length}")
print(f"width: {el.width}")
print(f"draft: {el.draft}")
print(f"sail: {el.sail}")
print(f"water_drag_coefficient: {el.water_drag_coefficient}")
print(f"wind_drag_coefficient: {el.wind_drag_coefficient}")

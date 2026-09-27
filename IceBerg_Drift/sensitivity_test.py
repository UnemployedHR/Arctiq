import pandas as pd
import numpy as np
from datetime import timedelta
from opendrift.models.openberg import OpenBerg
from opendrift.readers import reader_netCDF_CF_generic

# Cases to test
cases = {
    'Baseline': {'length': 100, 'width': 30, 'draft': 90, 'sail': 10},
    'Case_1_LG_Min': {'length': 123, 'width': 100, 'draft': 138, 'sail': 46},
    'Case_2_LG_Mean': {'length': 163, 'width': 130, 'draft': 210, 'sail': 60},
    'Case_3_LG_Max': {'length': 204, 'width': 160, 'draft': 300, 'sail': 75},
}

glorys_file = r'data\copernicus\glorys_iceberg_20857\iceberg_20857_glorys_uo_vo_20210601_20210810.nc'
era5_file = r'data\wind\iceberg_20857\era5_iceberg_20857_wind_20210601_20210810.nc'
ocean_reader = reader_netCDF_CF_generic.Reader(glorys_file, standard_name_mapping={'uo': 'x_sea_water_velocity', 'vo': 'y_sea_water_velocity'})
wind_reader = reader_netCDF_CF_generic.Reader(era5_file, standard_name_mapping={'u10': 'x_wind', 'v10': 'y_wind'})

start_time = pd.to_datetime('2021-06-02 16:41:00')
# We know baseline stranded on June 19. Run until June 25 to see if they pass it.
end_time = pd.to_datetime('2021-06-25 00:00:00')

start_lon = -62.41000
start_lat = 59.42667

results = {}

for name, params in cases.items():
    print(f"\nRunning {name}...")
    o = OpenBerg(loglevel=50)
    o.add_reader([ocean_reader, wind_reader])
    
    o.set_config('drift:vertical_profile', False)
    
    o.seed_elements(lon=start_lon, lat=start_lat, time=start_time,
                    length=params['length'], width=params['width'],
                    draft=params['draft'], sail=params['sail'])
    
    try:
        o.run(end_time=end_time, time_step=3600, time_step_output=3600)
    except Exception as e:
        print(f"Model stopped: {e}")
        
    status = o.result.status[0, :]
    lons = o.result.lon[0, :]
    lats = o.result.lat[0, :]
    times = o.result.time
    
    active_mask = (status == 0)
    stranded_mask = (status == 1)
    
    did_strand = np.any(stranded_mask)
    if did_strand:
        strand_idx = np.where(stranded_mask)[0][0]
        grounding_time = times[strand_idx]
        final_lon = lons[strand_idx]
        final_lat = lats[strand_idx]
    else:
        last_active = np.where(active_mask)[0][-1]
        grounding_time = "Did not ground"
        final_lon = lons[last_active]
        final_lat = lats[last_active]
        
    results[name] = {
        'did_strand': did_strand,
        'grounding_time': grounding_time,
        'final_lon': final_lon,
        'final_lat': final_lat
    }
    
print("\n=== RESULTS ===")
for name, res in results.items():
    print(f"{name}:")
    print(f"  Stranded: {res['did_strand']}")
    print(f"  Time: {res['grounding_time']}")
    print(f"  Final Pos: ({res['final_lon']:.5f}, {res['final_lat']:.5f})")


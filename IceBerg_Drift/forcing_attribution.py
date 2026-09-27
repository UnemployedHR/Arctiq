import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from opendrift.models.openberg import OpenBerg
from opendrift.readers import reader_netCDF_CF_generic
import warnings
warnings.filterwarnings("ignore")

start_time = pd.to_datetime('2021-06-02 16:41:00')
end_time = pd.to_datetime('2021-08-10 00:00:00')
start_lon = -62.41000
start_lat = 59.42667

geom = {'length': 100, 'width': 30, 'draft': 90, 'sail': 10}

glorys_file = r'data\copernicus\glorys_iceberg_20857\iceberg_20857_glorys_uo_vo_20210601_20210810.nc'
era5_file = r'data\wind\iceberg_20857\era5_iceberg_20857_wind_20210601_20210810.nc'

def run_experiment(name, use_ocean, use_wind, ocean_reader, wind_reader):
    print(f"\n==================================================")
    print(f"RUNNING: {name}")
    print(f"==================================================")
    
    o = OpenBerg(loglevel=50)

    
    readers = []
    if use_ocean: readers.append(ocean_reader)
    if use_wind: readers.append(wind_reader)
    
    if readers:
        o.add_reader(readers)
        
    o.set_config('drift:vertical_profile', False)
    
    if not use_ocean:
        o.set_config('environment:fallback:x_sea_water_velocity', 0.0)
        o.set_config('environment:fallback:y_sea_water_velocity', 0.0)
        o.set_config('environment:constant:x_sea_water_velocity', 0.0)
        o.set_config('environment:constant:y_sea_water_velocity', 0.0)
        
    if not use_wind:
        o.set_config('environment:fallback:x_wind', 0.0)
        o.set_config('environment:fallback:y_wind', 0.0)
        o.set_config('environment:constant:x_wind', 0.0)
        o.set_config('environment:constant:y_wind', 0.0)
        
    o.seed_elements(lon=start_lon, lat=start_lat, time=start_time,
                    length=geom['length'], width=geom['width'],
                    draft=geom['draft'], sail=geom['sail'])
    
    try:
        o.run(end_time=end_time, time_step=3600, time_step_output=3600, 
              outfile=f'data/results/iceberg_20857/{name}.nc')
    except Exception as e:
        print(f"Model stopped: {e}")
        
    return o

ocean_reader_inst = reader_netCDF_CF_generic.Reader(glorys_file, standard_name_mapping={'uo': 'x_sea_water_velocity', 'vo': 'y_sea_water_velocity'})
wind_reader_inst = reader_netCDF_CF_generic.Reader(era5_file, standard_name_mapping={'u10': 'x_wind', 'v10': 'y_wind'})

exp_A = run_experiment('forcing_full', True, True, ocean_reader_inst, wind_reader_inst)
exp_B = run_experiment('forcing_ocean_only', True, False, ocean_reader_inst, wind_reader_inst)
exp_C = run_experiment('forcing_wind_only', False, True, ocean_reader_inst, wind_reader_inst)

def process_results(o, name):
    status = o.result.status[0, :].values
    lons = o.result.lon[0, :].values
    lats = o.result.lat[0, :].values
    times = o.result.time.values
    
    df_data = {'time': times, 'lon': lons, 'lat': lats, 'status': status}
    for var in ['x_wind', 'y_wind', 'x_sea_water_velocity', 'y_sea_water_velocity']:
        if var in o.result:
            df_data[var] = o.result[var][0, :].values
            
    df = pd.DataFrame(df_data)
    df.to_csv(f'data/results/iceberg_20857/{name}.csv', index=False)
    
    did_strand = np.any(status == 1)
    if did_strand:
        strand_idx = np.where(status == 1)[0][0]
        g_time = times[strand_idx]
        f_lon = lons[strand_idx]
        f_lat = lats[strand_idx]
        duration = g_time - times[0]
        last_active = strand_idx - 1
    else:
        last_active = np.where(status == 0)[0][-1]
        g_time = "Did not strand"
        f_lon = lons[last_active]
        f_lat = lats[last_active]
        duration = times[last_active] - times[0]
        
    print(f"\n{name} Results:")
    print(f"Stranded: {did_strand}")
    print(f"Time: {g_time}")
    print(f"Duration: {duration}")
    print(f"Final Pos: ({f_lon:.5f}, {f_lat:.5f})")
    
    if name == 'forcing_full' and 'x_wind' in df.columns:
        start_stat_idx = max(0, last_active - 24*5)
        xw = df['x_wind'].iloc[start_stat_idx:last_active]
        yw = df['y_wind'].iloc[start_stat_idx:last_active]
        xc = df['x_sea_water_velocity'].iloc[start_stat_idx:last_active]
        yc = df['y_sea_water_velocity'].iloc[start_stat_idx:last_active]
        
        wind_speed = np.sqrt(xw**2 + yw**2).mean()
        curr_speed = np.sqrt(xc**2 + yc**2).mean()
        wind_dir = np.degrees(np.arctan2(yw.mean(), xw.mean()))
        curr_dir = np.degrees(np.arctan2(yc.mean(), xc.mean()))
        
        print(f"\nForcing Stats (last ~5 days before end):")
        print(f"Mean Wind Speed: {wind_speed:.3f} m/s")
        print(f"Mean Wind Direction (vector): {wind_dir:.1f} deg")
        print(f"Mean Ocean Speed: {curr_speed:.3f} m/s")
        print(f"Mean Ocean Direction (vector): {curr_dir:.1f} deg")

process_results(exp_A, 'forcing_full')
process_results(exp_B, 'forcing_ocean_only')
process_results(exp_C, 'forcing_wind_only')

df_iip = pd.read_csv('data/iip/IIP_2021IcebergSeason.csv')
df_iip = df_iip[df_iip['ICEBERG_NUMBER'].astype(str) == '20857'].copy()
df_iip['DATETIME'] = pd.to_datetime(df_iip['SIGHTING_DATE'].astype(str) + ' ' + df_iip['SIGHTING_TIME'].astype(str))
df_iip = df_iip.sort_values('DATETIME')

df_A = pd.read_csv('data/results/iceberg_20857/forcing_full.csv')
df_B = pd.read_csv('data/results/iceberg_20857/forcing_ocean_only.csv')
df_C = pd.read_csv('data/results/iceberg_20857/forcing_wind_only.csv')

plt.figure(figsize=(10, 8))
plt.plot(df_iip['SIGHTING_LONGITUDE'], df_iip['SIGHTING_LATITUDE'], 'ko--', label='IIP Observed', markersize=6)
plt.plot(df_A['lon'], df_A['lat'], 'b-', label='Full Forcing (Ocean+Wind)', linewidth=2)
plt.plot(df_B['lon'], df_B['lat'], 'g-', label='Ocean Only', linewidth=2)
plt.plot(df_C['lon'], df_C['lat'], 'r-', label='Wind Only', linewidth=2)

plt.plot(start_lon, start_lat, 'y*', markersize=15, label='Start Point', markeredgecolor='k')

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Forcing Attribution Analysis (Iceberg 20857)')
plt.legend()
plt.grid(True)
plt.savefig('data/results/iceberg_20857/forcing_attribution_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nPlot saved: data/results/iceberg_20857/forcing_attribution_comparison.png")

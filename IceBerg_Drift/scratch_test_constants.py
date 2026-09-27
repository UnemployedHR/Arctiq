import pandas as pd
from opendrift.models.openberg import OpenBerg
from opendrift.readers import reader_netCDF_CF_generic

o = OpenBerg(loglevel=50)

glorys_file = r'data\copernicus\glorys_iceberg_20857\iceberg_20857_glorys_uo_vo_20210601_20210810.nc'
ocean_reader = reader_netCDF_CF_generic.Reader(glorys_file, standard_name_mapping={'uo': 'x_sea_water_velocity', 'vo': 'y_sea_water_velocity'})
o.add_reader(ocean_reader)

o.set_config('environment:constant:x_wind', 0.0)
o.set_config('environment:constant:y_wind', 0.0)
o.set_config('environment:fallback:x_wind', 0.0)
o.set_config('environment:fallback:y_wind', 0.0)

o.seed_elements(lon=-62.41, lat=59.42667, time=pd.to_datetime('2021-06-02 16:41:00'))

try:
    o.run(steps=2, time_step=3600)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

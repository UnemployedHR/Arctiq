import copernicusmarine
import os
from dotenv import load_dotenv

load_dotenv(os.path.expanduser('~/.env'))

print("Starting download of 3D GLORYS data...")
copernicusmarine.subset(
    dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m",
    variables=["uo", "vo"],
    minimum_longitude=-63.41,
    maximum_longitude=-55.23667,
    minimum_latitude=54.39167,
    maximum_latitude=60.42667,
    start_datetime="2021-06-01T00:00:00",
    end_datetime="2021-08-10T23:59:59",
    minimum_depth=0.0,
    maximum_depth=400.0,
    output_directory="data/copernicus/glorys_iceberg_20857_vertical",
    output_filename="iceberg_20857_glorys_3d_uo_vo_20210601_20210810.nc",
    force_download=True
)
print("Download completed.")

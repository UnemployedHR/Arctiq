import getpass
import os
import cdsapi
import sys

print("=== CDS API Secure Download ===")
url = input("Enter CDS API URL (default: https://cds.climate.copernicus.eu/api): ").strip()
if not url:
    url = "https://cds.climate.copernicus.eu/api"
    
key = getpass.getpass("Enter CDS API Key (typing hidden): ").strip()

if not key:
    print("Error: API Key is required.")
    sys.exit(1)

out_dir = r"data\wind\iceberg_20857"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "era5_iceberg_20857_wind_20210601_20210810.nc")

print(f"\nInitializing CDS Client...")
c = cdsapi.Client(url=url, key=key)

print(f"Requesting ERA5 10m wind data...")
try:
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': [
                '10m_u_component_of_wind',
                '10m_v_component_of_wind',
            ],
            'year': '2021',
            'month': ['06', '07', '08'],
            'day': [f"{i:02d}" for i in range(1, 32)],
            'time': [f"{i:02d}:00" for i in range(24)],
            'area': [
                60.43, -63.41, 54.39, -55.23,
            ],
        },
        out_file
    )
    print("\nDownload completed successfully.")
    print(f"Saved to: {out_file}")
except Exception as e:
    print(f"\nDownload failed: {e}")
    sys.exit(1)

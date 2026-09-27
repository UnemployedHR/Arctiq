import getpass
import subprocess
import sys
import os

print("=== Copernicus Marine Secure Download ===")
username = input("Enter Copernicus Marine username: ")
password = getpass.getpass("Enter Copernicus Marine password (typing hidden): ")

out_dir = r"data\copernicus\glorys_iceberg_20857"
os.makedirs(out_dir, exist_ok=True)

cmd = [
    r"venv\Scripts\copernicusmarine.exe", "subset",
    "-i", "cmems_mod_glo_phy_my_0.083deg_P1D-m",
    "-v", "uo",
    "-v", "vo",
    "-x", "-63.41",
    "-X", "-55.23667",
    "-y", "54.39167",
    "-Y", "60.42667",
    "-t", "2021-06-01 00:00:00",
    "-T", "2021-08-10 23:59:59",
    "-z", "0.0",
    "-Z", "0.5",
    "-o", out_dir,
    "-f", "iceberg_20857_glorys_uo_vo_20210601_20210810.nc",
    "--username", username,
    "--password", password,
    "--force-download"
]

print("Starting download...")
result = subprocess.run(cmd)

if result.returncode == 0:
    print("\nDownload completed successfully.")
else:
    print(f"\nDownload failed with exit code {result.returncode}.")
    sys.exit(result.returncode)

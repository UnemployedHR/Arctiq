"""
OpenBerg Minimal Simulation Test
=================================
Step 1: Verify OpenBerg import and run a fully offline simulation
         using ReaderConstant (no internet / THREDDS required).

Iceberg scenario:
  - Start position : lon=0.0, lat=72.0 (open North Atlantic / Greenland Sea)
                     (moved well offshore to avoid stranding in 48h)
  - Ocean current  : 0.1 m/s eastward, 0.02 m/s northward
  - Wind           : 3 m/s eastward, 1 m/s northward
  - Duration       : 48 hours, 1-hour time steps
  - Iceberg size   : length=100 m, draft=90 m, sail=10 m, width=30 m
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from opendrift.models.openberg import OpenBerg
from opendrift.readers.reader_constant import Reader as ReaderConstant
from opendrift.readers.reader_global_landmask import Reader as LandmaskReader

# -- 1. Initialise model -------------------------------------------------------
o = OpenBerg(loglevel=20)

# -- 2. Constant forcing: gentle eastward current + wind -----------------------
reader_const = ReaderConstant({
    'x_sea_water_velocity': 0.10,   # m/s eastward
    'y_sea_water_velocity': 0.02,   # m/s northward (gentle)
    'x_wind':  3.0,                  # m/s eastward
    'y_wind':  1.0,                  # m/s northward
    'sea_surface_wave_significant_height': 1.0,
    'sea_surface_wave_from_direction': 270.0,
})

# -- 3. Global land-mask -------------------------------------------------------
reader_land = LandmaskReader()

# -- 4. Attach readers ---------------------------------------------------------
o.add_reader([reader_const, reader_land])

# -- 5. Seed iceberg in open ocean (Greenland Sea) -----------------------------
start_time = datetime(2024, 1, 1, 0, 0, 0)

o.seed_elements(
    lon=0.0,            # open North Atlantic, well clear of coast
    lat=72.0,
    time=start_time,
    number=5,
    length=100,         # iceberg length  (m)
    draft=90,           # below-waterline (m)
    sail=10,            # above-waterline (m)
    width=30,           # iceberg width   (m)
)

# -- 6. Run 48-hour simulation -------------------------------------------------
o.run(
    duration=timedelta(hours=48),
    time_step=3600,
    time_step_output=3600,
    outfile='iceberg_trajectory.nc',
)

print("\n=== Simulation complete! ===")
print("   NetCDF output : iceberg_trajectory.nc")

# -- 7. Final positions via new result API -------------------------------------
#    o.result.lon  shape: (n_particles, n_time)
lon_arr = np.array(o.result.lon)   # (particles, time)
lat_arr = np.array(o.result.lat)
n_particles = lon_arr.shape[0]

print("\nFinal positions (last time step):")
for i in range(n_particles):
    lo = lon_arr[i, -1]
    la = lat_arr[i, -1]
    if np.isfinite(lo):
        print(f"   Particle {i+1}: lon={lo:.4f}, lat={la:.4f}")
    else:
        print(f"   Particle {i+1}: stranded / deactivated")

# -- 8. Plot trajectory --------------------------------------------------------
o.plot(fast=True, filename='iceberg_trajectory_plot.png')
print("\nPlot saved : iceberg_trajectory_plot.png")

# -- 9. Export to CSV ----------------------------------------------------------
#    lon_arr shape: (n_particles, n_time)
times = np.array(o.result.time)    # 1-D array of np.datetime64

rows = []
for p_idx in range(n_particles):
    for t_idx, t in enumerate(times):
        lo = lon_arr[p_idx, t_idx]
        la = lat_arr[p_idx, t_idx]
        if np.isfinite(lo) and np.isfinite(la):
            rows.append({
                'time':     str(t),
                'particle': p_idx + 1,
                'lon':      float(lo),
                'lat':      float(la),
            })

df = pd.DataFrame(rows)
df.to_csv('iceberg_trajectory.csv', index=False)
print("CSV saved  : iceberg_trajectory.csv")
print(f"Total rows : {len(df)}")
print(df.head(10).to_string(index=False))
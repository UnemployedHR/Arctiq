# Environmental Forcing

OpenBerg requires external environmental data to push the simulated icebergs. This project relies on two primary forcing datasets.

## 1. Ocean Currents (GLORYS12V1)
* **Variables used:** `uo` (Eastward Velocity), `vo` (Northward Velocity).
* **Depth:** The NetCDF contains 50 vertical levels. However, as noted in the Physics Model documentation, the current prototype configuration (`drift:vertical_profile = False`) forces OpenBerg to only sample the top surface level.
* **Spatial Resolution:** ~8 km globally.
* **Temporal Resolution:** Daily means. This means the ocean current vector changes only once per day in the simulation.
* **Mapping:** Handled via OpenDrift's CF standard name matching (`eastward_sea_water_velocity` -> `x_sea_water_velocity`).

## 2. Atmospheric Wind (ERA5)
* **Variables used:** `u10` (10m Eastward Wind), `v10` (10m Northward Wind).
* **Spatial Resolution:** ~30 km globally.
* **Temporal Resolution:** Hourly.
* **Mapping:** Explicitly mapped in `real_run.py` when initializing the reader (`{'u10': 'x_wind', 'v10': 'y_wind'}`).

## Integration Limitations
* Because GLORYS is daily and ERA5 is hourly, OpenDrift linearly interpolates the daily ocean currents down to the simulation timestep (e.g., 1 hour), while the wind updates hourly.
* A lack of high-frequency tidal or inertial current data in the GLORYS daily mean means the simulated trajectories will be much smoother than real-world trajectories.

# OpenBerg Vertical Profile Inspection

## A. OpenBerg Implementation Findings

An inspection of `opendrift/models/openberg.py` (specifically the `advect_iceberg` method and `get_profile_masked` helper) reveals exactly how `drift:vertical_profile = True` is processed:

1. **Depth Integration:** Rather than taking the current at a single specific depth or the surface, OpenBerg calculates a true depth-averaged velocity (`umean`, `vmean`). 
2. **Weighting:** It calculates the mean velocity of each vertical layer (`(uprof[1:] + uprof[:-1]) / 2`), weights it by the thickness of that layer (`z[1:] - z[:-1]`), and sums these up down to the iceberg's draft.
3. **Masking:** It masks (ignores) any ocean current data at depths strictly greater than the iceberg's draft.
4. **Variable Requirements:** The variables `x_sea_water_velocity` and `y_sea_water_velocity` are flagged with `"profiles": True` in the model's `required_variables` dictionary. This instructs OpenDrift to supply arrays with a vertical `z` dimension rather than just a 2D surface slice.

## B. Current GLORYS Dataset Limitations

The currently downloaded GLORYS dataset (`iceberg_20857_glorys_uo_vo_20210601_20210810.nc`) contains:
- **Available depth coordinates:** Exactly 1 depth level (`0.494025 m`).

**Suitability:** The current file is **NOT suitable** for vertical-profile mode. If attempted, the layer thickness calculation (`z[1:] - z[:-1]`) will evaluate to an empty array (since length is 1), leading to an immediate mathematical crash (`np.nansum` over empty arrays / division by zero) or invalid advection.

## C. Required Ocean Depth Range

To correctly calculate the depth-integrated current, the ocean dataset must extend from the surface down to at least the maximum draft of the iceberg being simulated. 
- For the baseline geometry, the draft is **90 meters**.
- For the maximum sensitivity geometry previously calculated (Large Non-Tabular), the draft could reach up to **300 meters**.

If the ocean dataset does not extend to the full iceberg draft, OpenBerg will only integrate over the available depth layers, missing the deep-current forcing entirely.

## D. Exact Next-Step Experiment Design

To perform a scientifically safe vertical-profile experiment without altering the baseline assumptions, the following design is required:

1. **New Download:** Download a new GLORYS NetCDF file covering the exact same spatial and temporal bounds, but with a depth subset of `[0.0, 400.0]` meters (ensuring we safely cover the 90m baseline draft and any future sensitivity tests).
2. **OpenBerg Configuration:** Set `o.set_config('drift:vertical_profile', True)`.
3. **Reader Configuration:** Keep using `reader_netCDF_CF_generic`. It will automatically parse the 3D dimensions (time, depth, lat, lon) and supply them as profiles to OpenBerg.
4. **Control Variables:** Maintain identical ERA5 wind forcing, starting position, simulation period, coastline_action, and baseline geometry (`length=100`, `width=30`, `draft=90`, `sail=10`).

OpenDrift fundamentally accepts daily temporal resolution for 3D profiles and interpolates linearly in space and time exactly as it does for 2D surface fields.

## E. Risks and Assumptions

- **Nonlinear shear:** A depth-integrated current applies a uniform bulk force to the iceberg's underwater volume. If there is extreme vertical shear (e.g., surface currents flowing South, deep currents flowing East), the depth-averaged current may push the iceberg in a direction that neither the surface nor the deep ocean is strictly flowing, which is a simplification of true fluid dynamics on a rigid body.
- **Data Size:** Downloading 3D data down to 400m across a 2+ month daily window will significantly increase the NetCDF file size compared to the 1.95 MB surface-only file. We should ensure the spatial bounding box is kept tight.

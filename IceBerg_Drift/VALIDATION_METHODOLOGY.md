# Historical Validation Methodology: IIP Iceberg 20857

This document outlines the planned methodology for validating the historical trajectory of IIP iceberg 20857 using the OpenBerg model.

The primary objective is to compare the OpenBerg simulated trajectory against the observed International Ice Patrol (IIP) positions at the exact observation timestamps.

## 1. Initialization

The simulation will be initialized strictly from the first ground-truth observation:
- **Iceberg Number:** 20857
- **Initial Time:** 2021-06-02 16:41:00
- **Initial Latitude:** 59.42667
- **Initial Longitude:** -62.41000

## 2. Environmental Forcing

Two primary forcing datasets will be used to drive the iceberg advection:
1. **Ocean Currents:** Historical GLORYS12V1 (CMEMS) reanalysis data.
2. **Wind:** Historical ERA5 hourly 10 m wind (ECMWF) reanalysis data.

The validation will consist of comparing two distinct configurations of ocean forcing:
- **Surface-current experiment:** Uses only the top surface layer of the ocean.
- **Vertical-profile experiment:** Uses a depth-integrated / thickness-weighted bulk ocean current extending from the surface down to the iceberg's draft.

## 3. Temporal Matching

Since the IIP observations occur at irregular intervals (ranging from 11.5 to 348 hours), the regular OpenBerg simulation output (e.g., hourly timesteps) will be linearly interpolated in time to match the exact `datetime` of each IIP observation. This ensures that the spatial comparison is performed at the precise timestamp of the real-world sighting.

## 4. Spatial Error

Spatial error will be evaluated using the **Great-Circle (Haversine) or Geodesic distance** (in kilometers) between the observed IIP position and the temporally-matched modeled position. Raw latitude/longitude numerical differences will NOT be used as the primary error metric, as they do not translate uniformly to physical distances at high latitudes.

## 5. Metrics

To summarize the accuracy of the simulated trajectory, the following error metrics will be computed across all valid matching timestamps:
- **Mean error:** The arithmetic average of all spatial errors.
- **Median error:** The 50th percentile of spatial errors.
- **RMSE (Root Mean Square Error):** Emphasizes larger deviations.
- **Maximum error:** The largest single deviation between the model and observation.
- **Minimum error:** The smallest single deviation between the model and observation.

## 6. Trajectory Comparison

A comparative visualization will be generated to qualitatively assess the drift path. The plot will display:
- The actual IIP observed trajectory (ground truth).
- The OpenBerg modeled trajectory.
- The coastline and relevant geographic bounding box.

## 7. Grounding and Deactivation

In the event that the model interacts with the coastline, the following will be recorded:
- **Stranded status:** Whether the iceberg became stranded (status = 1) or deactivated.
- **Grounding/deactivation time:** The exact timestep when the model stopped moving.
- **Final modeled position:** The latitude and longitude at the point of grounding.

## 8. Important Limitation Regarding Grounding

If the OpenBerg model becomes stranded (grounded) before later IIP observations occur, the simulation effectively terminates at the coastline. Consequently, the model cannot produce valid, physically meaningful model-vs-observation spatial errors for timestamps after the grounding event. Error metrics will only be computed for the period where the model remained active and physically adrift.

## 9. Planned Experiments

To evaluate the impact of deep-ocean current forcing versus surface-only forcing, the following two controlled experiments will be compared:

- **Experiment A (Surface-only):** Surface-only ocean + ERA5 wind.
- **Experiment B (Vertical-profile):** Vertical-profile ocean + ERA5 wind.

**Scientific Control:**
All other model parameters—including the initial position, start time, simulation duration, coastline action, and baseline iceberg geometry (`length=100m, width=30m, draft=90m, sail=10m`)—will remain absolutely identical between both experiments. No conclusions regarding which configuration is more accurate will be drawn until both simulations are completed and the aforementioned metrics are computed.

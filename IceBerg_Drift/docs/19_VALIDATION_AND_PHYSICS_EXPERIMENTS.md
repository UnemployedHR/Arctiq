# Validation and Physics Experiments

During the development of the prototype, several targeted diagnostic experiments were conducted to understand OpenBerg's behavior. These are documented in specific markdown files in the repository root.

## 1. Forcing Attribution (7-Day)
**File:** `FORCING_ATTRIBUTION_7DAY.md` / `forcing_attribution_7day.py`
* **Purpose:** To determine whether ocean currents (GLORYS) or wind (ERA5) dominates iceberg drift in the simulation.
* **Experiment:** Simulated Iceberg 20857 over 7 days using:
    1. Both Current and Wind
    2. Current Only
    3. Wind Only
    4. Zero Forcing
* **Results:** Without ocean currents, the iceberg barely moves relative to ground truth. Without wind, the trajectory diverges significantly. Both are required for accurate physical modeling.

## 2. Vertical Profile Inspection
**File:** `VERTICAL_PROFILE_INSPECTION.md`
* **Purpose:** To evaluate how OpenBerg uses 3D ocean current data vs. 2D surface data.
* **Setup:** Toggle `drift:vertical_profile = True` vs `False`.
* **Conclusion:** In the current prototype, surface-only simulations often yielded more stable results than full 3D integration, likely because deep draft assumptions (90m) were interacting poorly with coarse bathymetry or unresolved deep current shears.

## 3. Grounding Diagnostics
**File:** `GROUNDING_DIAGNOSTIC_V2.md`
* **Purpose:** Investigated why icebergs suddenly stop moving in OpenDrift.
* **Conclusion:** OpenDrift's landmask checking aggressively grounds particles that get too close to coarse coastal boundaries in the NetCDF files.

## 4. Trajectory Bridge Analysis
**File:** `TRAJECTORY_BRIDGE_ANALYSIS.md`
* **Purpose:** Evaluated how interpolation between sparse observation points affects the perceived "ground truth" path vs the physical simulated path.

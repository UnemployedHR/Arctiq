# Physics Model (OpenBerg)

This project utilizes **OpenBerg**, an iceberg-specific trajectory simulation module built on top of the broader **OpenDrift** framework.

## OpenDrift Framework
OpenDrift is a Lagrangian particle tracking framework. It uses environmental fields (from NetCDF readers) to move particles iteratively over time using Runge-Kutta numerical integration.

## OpenBerg Module
OpenBerg specializes the OpenDrift engine for icebergs.

### Physics Forces Considered:
* **Ocean Currents:** Provides the primary advection force.
* **Wind:** Acts on the sail (above-water portion) of the iceberg.
* **Coriolis Force:** Rotates the movement trajectory based on the Earth's rotation and the iceberg's latitude.
* **Water Drag / Form Drag:** Resistance from the water acting against the iceberg's motion.

### Configuration (`real_run.py`)
In the prototype scripts, specific OpenBerg settings are used:
* `drift:vertical_profile = False`: In the prototype tests, the vertical current profile integration is turned off. The model acts strictly on the surface current (`uo`, `vo` at the top level). This simplifies the simulation when high-resolution depth profiles are unverified.
* **Iceberg Geometry:** Because IIP data often lacks precise 3D geometry, the prototype hardcodes assumed dimensions during testing (e.g., `length=100m, width=30m, draft=90m, sail=10m`). *Note: These are experimental defaults, not verified IIP measurements.*
* **Landmask & Grounding:** OpenDrift checks if a particle hits a coastline. Experimental diagnostics (`diagnose_grounding_v2.py`) have investigated how bounding box resolution affects artificial "grounding" errors.

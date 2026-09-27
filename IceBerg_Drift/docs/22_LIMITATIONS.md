# Limitations

This is a prototype system. It is scientifically and operationally vital to understand its limitations.

## 1. Scientific Limitations

* **Sparse Observations:** The IIP ground truth data is extremely sparse (often weeks between sightings). The `build_ml_dataset.py` pipeline relies heavily on interpolation, meaning the "ground truth" path against which models are trained and evaluated is an approximation of reality.
* **Iceberg Geometry Assumptions:** We do not know the actual length, width, or draft of historical IIP icebergs. The physics model (OpenBerg) assumes a standard profile (e.g., 90m draft, 10m sail). Real drift highly depends on these exact geometries.
* **Environmental Forcing Resolution:** GLORYS is daily mean data at ~8 km resolution. It misses high-frequency inertial oscillations, tides, and small-scale eddies that drive real iceberg motion.
* **Population vs. Single Iceberg Comparison:** The ML models are evaluated over a vast population of icebergs. The full OpenBerg physics model is evaluated only on isolated case studies because downloading GLORYS/ERA5 for the entire population is unfeasible. Therefore, a direct, perfectly equal numerical comparison between Pure Physics and Pure ML across the entire dataset is not present.

## 2. Engineering Limitations

* **No Automated Operational API:** There is no single command that accepts a new lat/lon/time and automatically fetches current NetCDFs to output a prediction.
* **Hybrid Implementation:** The Hybrid Physics + ML model uses a simplified "scaled persistence" as its physics prior, not a full OpenBerg numerical integration. 
* **Hardcoded Paths:** Some scripts may contain localized Windows paths (e.g., `data\copernicus\...`) which require careful attention if running on Linux or Mac.

# Arctiq: Oceanographic & Maritime Intelligence Suite

Welcome to the **Arctiq** repository. This workspace contains a collection of advanced systems and prototypes focused on maritime tracking, Arctic environmental modeling, and predictive oceanography. 

This repository operates as a monorepo containing three distinct, highly specialized projects.

## 📂 Projects Overview

### 1. [Iceberg Trajectory Prediction System](./IceBerg_Drift/)
An advanced machine learning and physics-based prototype designed to predict the trajectories of drifting icebergs.
- **Problem Solved**: Forecasting iceberg displacements based on historical observations and environmental forcing, compensating for the lack of high-resolution operational data.
- **Approach**: A hybrid methodology benchmarking purely physics-based simulations (OpenBerg/OpenDrift) against data-driven Machine Learning models (XGBoost, GRU, Ridge).
- **Tech Stack**: Python, PyTorch, Scikit-Learn, XGBoost, OpenDrift, xarray, pandas.
- **Key Data Sources**: International Ice Patrol (IIP), Copernicus GLORYS12V1, ECMWF ERA5.

### 2. [MarineRadar — Global Vessel Tracking](./MarineRadar_AIS_Tracker/)
A real-time, highly-optimized vessel tracking and analysis web application displaying live ship positions on an interactive world map.
- **Features**: Live AIS (Automatic Identification System) streaming via WebSockets, dynamic port simulation, MMSI flag state decoding, and highly efficient canvas-based map rendering capable of handling hundreds of active vessels.
- **Tech Stack**: React 19, Vite, Node.js, Express, WebSockets, Leaflet (react-leaflet).

### 3. [Sea Ice Thickness Model](./Sea_Ice_Thickness/)
A machine learning pipeline that models sea ice density and thickness using real satellite data.
- **Methodology**: Merges ICESat-2 (ATL10) freeboard satellite altimetry measurements with GLORYS12 physical oceanography grids to train an XGBoost regressor for accurate ice thickness predictions.
- **Tech Stack**: Python, XGBoost, pandas, h5py (HDF5), netCDF4.

## 🚀 Getting Started

Each project is fully self-contained with its own dependencies, scripts, and documentation. 

To explore or run a specific system, navigate to its respective directory and follow the instructions in its local `README.md`:

- 🧊 [Iceberg Drift Instructions](./IceBerg_Drift/README.md)
- 🚢 [MarineRadar AIS Tracker Instructions](./MarineRadar_AIS_Tracker/README.md)
- ❄️ [Sea Ice Thickness Code](./Sea_Ice_Thickness/)

## ⚙️ Technologies Used

Across the Arctiq suite, the following core technologies are utilized:
- **Languages**: Python 3.x, JavaScript / React
- **Machine Learning**: PyTorch, XGBoost, Scikit-Learn
- **Geospatial & Oceanographic**: Leaflet, OpenDrift, xarray, NetCDF4, HDF5
- **Backend & Real-time APIs**: Node.js, Express, WebSockets (AISStream)

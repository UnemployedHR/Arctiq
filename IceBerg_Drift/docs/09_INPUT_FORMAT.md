# Input Format

If you are modifying or providing new raw observation data to the ML pipeline, it must follow specific structural rules.

## Raw IIP Observation Input
The raw dataset generation expects a tabular format (CSV) or pre-processed DataFrame containing historical iceberg sightings.

**Required Columns:**
* `iceberg_id`: Unique identifier for the iceberg.
* `timestamp` or `datetime`: The exact time of observation (ISO 8601 or pandas-parseable format).
* `lat`: Decimal latitude.
* `lon`: Decimal longitude.

## ML Pipeline Expected Input (Feature Engineered)
The ML models do **not** take raw Lat/Lon coordinates. They take engineered Lag Features representing the iceberg's recent movement history.

To make a prediction using the trained ML models, your input must be transformed to match the feature schema defined in `data/ml/ml_dataset_config.json`:

**Key ML Input Features (Example):**
* `prev_delta_lat`: Change in latitude over the previous interval.
* `prev_delta_lon`: Change in longitude over the previous interval.
* `prev_dt_hours`: Time elapsed during the previous interval.
* `forecast_dt_hours`: Time into the future for which we are predicting.

*Note: Because the models rely on `prev_delta`, you MUST have at least TWO prior observations of the iceberg to compute the input features for a single prediction step.*

### Physics Proxy (Hybrid Model)
If you are passing input to the Hybrid model, the script automatically computes:
* `phys_dlat` = `prev_delta_lat` * (`forecast_dt_hours` / `prev_dt_hours`)
* `phys_dlon` = `prev_delta_lon` * (`forecast_dt_hours` / `prev_dt_hours`)

# Future Work

The following improvements would elevate the prototype to an operational system.

## Priority 1: Automated Environmental Ingestion
* **Goal:** Allow true unseen predictions.
* **Task:** Implement an API client (using `copernicusmarine` and `cdsapi`) that automatically downloads bounding-box NetCDFs for GLORYS and ERA5 on-the-fly when a user submits a new iceberg observation.

## Priority 2: True Hybrid ML Pipeline
* **Goal:** Replace the scaled-persistence "physics proxy".
* **Task:** Instead of scaling persistence, run a fast, low-resolution OpenBerg trajectory for every training sample. Extract the OpenBerg predicted displacement, and use *that* as the primary feature for the Gradient Boosting residual model.

## Priority 3: Probabilistic Prediction & Uncertainty
* **Goal:** Provide confidence intervals.
* **Task:** Instead of predicting a single deterministic Lat/Lon coordinate, use Quantile Regression or Monte Carlo dropout in the GRU to output an expected "search area" ellipse.

## Priority 4: Dynamic Geometry Estimation
* **Goal:** Improve physics accuracy.
* **Task:** Implement a degradation model that estimates how an iceberg's draft and sail change over time due to melting, rather than assuming constant geometry.

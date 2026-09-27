# Training and Evaluation Methodology

To ensure robust results and prevent data leakage, the machine learning pipeline strictly controls how data is partitioned.

## Iceberg-Level Splitting
* Handled by `create_iip_ml_split.py`.
* **The Problem:** If sequential observations of Iceberg A are randomly shuffled into Train and Test sets, the model might "cheat" by memorizing the local current at that specific time and location, rather than learning general physical rules.
* **The Solution:** The dataset is grouped by `iceberg_id`. Entire icebergs (and all their trajectory segments) are randomly assigned to either Train, Val, or Test.

## Evaluation Metrics
When models predict a `delta_lat` and `delta_lon`, the system must quantify how "wrong" that prediction is.

* **Metric:** Geodesic Error (Kilometers).
* **Calculation:** The `haversine_km` function in `final_evaluation.py` converts the predicted angular deltas back into absolute coordinates, then calculates the great-circle distance between the predicted position and the actual ground truth position.
* **Reporting:** The evaluation script reports:
    * **Mean Error:** Average deviation.
    * **Median Error:** 50th percentile deviation (less sensitive to extreme outliers).
    * **RMSE (Root Mean Square Error):** Heavily penalizes large errors.
    * **Max Error:** The worst single prediction in the set.

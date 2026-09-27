# Machine Learning Models

This project evaluates several ML architectures against baseline methods.

## 1. Persistence Baseline
* **Mechanism:** Not a learned model. It assumes the iceberg will maintain its exact previous velocity.
* **Implementation:** `forecast_delta = prev_delta`.
* **Purpose:** The minimum threshold any ML model must beat to prove it has learned something useful.

## 2. Ridge Regression
* **Mechanism:** Linear regression with L2 regularization to prevent overfitting.
* **Implementation:** `sklearn.linear_model.Ridge`.
* **Hyperparameters:** Alpha term tuned on the validation set.

## 3. Gradient Boosting Regressor (GBR)
* **Mechanism:** An ensemble of decision trees built sequentially to correct the errors of previous trees. Capable of learning non-linear interactions.
* **Implementation:** XGBoost (`XGBRegressor`) if available; otherwise falls back to `sklearn.ensemble.GradientBoostingRegressor`.
* **Hyperparameters:** `n_estimators`, `learning_rate`, `max_depth` tuned for performance.

## 4. GRU (Gated Recurrent Unit)
* **Mechanism:** A Recurrent Neural Network (RNN) designed for sequential data. 
* **Implementation:** Built using PyTorch. 
* **Details:** Capable of looking back multiple steps in the sequence rather than just the single previous lag feature. 

## 5. Hybrid Physics + ML Model
* **Important Limitation:** Running full OpenBerg numerical physics simulations for thousands of historical training samples is computationally prohibitive (requires massive NetCDF downloads).
* **Implementation:** The hybrid model currently uses a "physics proxy". 
    1. It scales the persistence forecast by the ratio of time (`forecast_dt / prev_dt`) to estimate physical advection.
    2. It trains a Gradient Boosting model to predict the *residual error* between this physics prior and the actual ground truth.
    3. Final Prediction = `Physics Proxy + ML Residual Prediction`.
* **Purpose:** Explores how injecting a mechanistic prior helps tree-based models generalize.

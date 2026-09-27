"""
train_baseline_models.py

Trains and evaluates baseline models for iceberg trajectory prediction.

Models:
  0. Persistence baseline (no training)
  1. Linear Regression (sklearn)
  2. GradientBoostingRegressor (sklearn, XGBoost-equivalent if not available)

All models trained ONLY on training split.
Hyperparameters selected using validation split.
Test set touched ONLY in final evaluation block.

Target: [target_delta_lat, target_delta_lon]

Evaluation metric: geodesic distance (km) between predicted and actual next position.
"""

import os, json, warnings, joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error

warnings.filterwarnings('ignore')
os.makedirs('models/baselines', exist_ok=True)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

R = 6371.0
def haversine_km(dlon, dlat, lat_ref):
    """Approximate geodesic distance from predicted delta_lat/delta_lon."""
    lat1 = np.radians(lat_ref)
    lat2 = np.radians(lat_ref + dlat)
    dlo  = np.radians(dlon)
    a = np.sin((np.radians(dlat))/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlo/2)**2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def geo_error_km(pred_dlat, pred_dlon, true_dlat, true_dlon, lat_ref):
    """Geodesic distance between predicted and actual next position."""
    pred_lat = lat_ref + pred_dlat
    true_lat = lat_ref + true_dlat
    pred_lon_abs = lat_ref * 0 + pred_dlon   # relative lon shift
    true_lon_abs = lat_ref * 0 + true_dlon
    # Use actual positions
    lo1 = np.radians(lat_ref + pred_dlon*0)   # reference lon (0-centered)
    la1 = np.radians(pred_lat)
    lo2 = np.radians(true_lon_abs - pred_lon_abs)
    la2 = np.radians(true_lat)
    # Correct haversine: predicted absolute position vs actual absolute position
    # We need absolute positions. Use lat_ref for base lon (relative changes are comparable).
    # Delta lat/lon are in degrees; use them directly as displacement from base:
    pred_la = np.radians(lat_ref + pred_dlat)
    true_la = np.radians(lat_ref + true_dlat)
    dlo = np.radians(true_dlon - pred_dlon)
    dla = true_la - pred_la
    a = np.sin(dla/2)**2 + np.cos(pred_la)*np.cos(true_la)*np.sin(dlo/2)**2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def metrics(errors_km, label):
    e = np.array(errors_km)
    e = e[~np.isnan(e)]
    print(f"\n  {label} (n={len(e)}):")
    print(f"    Mean  : {np.mean(e):.3f} km")
    print(f"    Median: {np.median(e):.3f} km")
    print(f"    RMSE  : {np.sqrt(np.mean(e**2)):.3f} km")
    print(f"    Min   : {np.min(e):.3f} km")
    print(f"    Max   : {np.max(e):.3f} km")
    return {
        'n': len(e),
        'mean_km':   round(float(np.mean(e)),   3),
        'median_km': round(float(np.median(e)), 3),
        'rmse_km':   round(float(np.sqrt(np.mean(e**2))), 3),
        'min_km':    round(float(np.min(e)),    3),
        'max_km':    round(float(np.max(e)),    3),
    }

# ─── Load dataset ─────────────────────────────────────────────────────────────
ml = pd.read_parquet('data/ml/final_ml_dataset.parquet')
with open('data/ml/ml_dataset_config.json') as f:
    config = json.load(f)

feature_cols = config['feature_cols']
target_cols  = config['target_cols']

train = ml[ml['split'] == 'train'].reset_index(drop=True)
val   = ml[ml['split'] == 'val'].reset_index(drop=True)
test  = ml[ml['split'] == 'test'].reset_index(drop=True)

print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

X_train = train[feature_cols].values.astype(np.float32)
y_train = train[target_cols].values.astype(np.float32)
X_val   = val[feature_cols].values.astype(np.float32)
y_val   = val[target_cols].values.astype(np.float32)
X_test  = test[feature_cols].values.astype(np.float32)
y_test  = test[target_cols].values.astype(np.float32)

lat_train = train['lat'].values
lat_val   = val['lat'].values
lat_test  = test['lat'].values

results = {}

# ─── MODEL 0: Persistence ─────────────────────────────────────────────────────
print("\n=== MODEL 0: Persistence baseline ===")
# Predict: same delta_lat, delta_lon as the PREVIOUS segment
# (i.e. forecast_delta = prev_delta)
# prev_delta features: feature index 2,3 = prev_delta_lat, prev_delta_lon
pidx_lat = feature_cols.index('prev_delta_lat')
pidx_lon = feature_cols.index('prev_delta_lon')

def persistence_predict(X):
    return np.stack([X[:, pidx_lat], X[:, pidx_lon]], axis=1)

p_val  = persistence_predict(X_val)
p_test = persistence_predict(X_test)

p_val_err  = geo_error_km(p_val[:,0],  p_val[:,1],  y_val[:,0],  y_val[:,1],  lat_val)
p_test_err = geo_error_km(p_test[:,0], p_test[:,1], y_test[:,0], y_test[:,1], lat_test)

results['persistence_val']  = metrics(p_val_err,  "Persistence (Val)")
results['persistence_test'] = metrics(p_test_err, "Persistence (Test)")

# ─── MODEL 1: Ridge Regression ────────────────────────────────────────────────
print("\n=== MODEL 1: Ridge Regression ===")
# Scale features on train only
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc   = scaler.transform(X_val)
X_test_sc  = scaler.transform(X_test)

# Separate Ridge for each target
best_alpha, best_val_err = 1.0, np.inf
for alpha in [0.01, 0.1, 1.0, 10.0, 100.0]:
    m_lat = Ridge(alpha=alpha).fit(X_train_sc, y_train[:,0])
    m_lon = Ridge(alpha=alpha).fit(X_train_sc, y_train[:,1])
    p = np.stack([m_lat.predict(X_val_sc), m_lon.predict(X_val_sc)], axis=1)
    ev = np.mean(geo_error_km(p[:,0], p[:,1], y_val[:,0], y_val[:,1], lat_val))
    print(f"  alpha={alpha:.3f}  val_mean_err={ev:.3f} km")
    if ev < best_val_err:
        best_val_err, best_alpha = ev, alpha

ridge_lat = Ridge(alpha=best_alpha).fit(X_train_sc, y_train[:,0])
ridge_lon = Ridge(alpha=best_alpha).fit(X_train_sc, y_train[:,1])
print(f"  Best alpha: {best_alpha}")

r_val  = np.stack([ridge_lat.predict(X_val_sc),  ridge_lon.predict(X_val_sc)],  axis=1)
r_test = np.stack([ridge_lat.predict(X_test_sc), ridge_lon.predict(X_test_sc)], axis=1)

r_val_err  = geo_error_km(r_val[:,0],  r_val[:,1],  y_val[:,0],  y_val[:,1],  lat_val)
r_test_err = geo_error_km(r_test[:,0], r_test[:,1], y_test[:,0], y_test[:,1], lat_test)

results['ridge_val']  = metrics(r_val_err,  "Ridge Regression (Val)")
results['ridge_test'] = metrics(r_test_err, "Ridge Regression (Test)")

joblib.dump(scaler,    'models/baselines/ridge_scaler.joblib')
joblib.dump(ridge_lat, 'models/baselines/ridge_lat.joblib')
joblib.dump(ridge_lon, 'models/baselines/ridge_lon.joblib')
print("  Saved ridge models.")

# ─── MODEL 2: Gradient Boosting ───────────────────────────────────────────────
print("\n=== MODEL 2: Gradient Boosting ===")
# Try XGBoost first, fall back to sklearn GBR
try:
    from xgboost import XGBRegressor
    GBR = XGBRegressor
    gbr_kwargs = dict(random_state=RANDOM_SEED, n_estimators=300, learning_rate=0.05,
                      max_depth=5, subsample=0.8, colsample_bytree=0.8,
                      verbosity=0, n_jobs=-1)
    USE_XGB = True
    print("  Using XGBoost")
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor as GBR
    gbr_kwargs = dict(random_state=RANDOM_SEED, n_estimators=200, learning_rate=0.05,
                      max_depth=4, subsample=0.8, min_samples_leaf=5)
    USE_XGB = False
    print("  XGBoost not available; using sklearn GradientBoostingRegressor")

# For sklearn GBR we need separate models per target
gbr_lat = GBR(**gbr_kwargs)
gbr_lon = GBR(**gbr_kwargs)
# Use scaled features for consistency
gbr_lat.fit(X_train_sc, y_train[:,0])
gbr_lon.fit(X_train_sc, y_train[:,1])

gb_val  = np.stack([gbr_lat.predict(X_val_sc),  gbr_lon.predict(X_val_sc)],  axis=1)
gb_test = np.stack([gbr_lat.predict(X_test_sc), gbr_lon.predict(X_test_sc)], axis=1)

gb_val_err  = geo_error_km(gb_val[:,0],  gb_val[:,1],  y_val[:,0],  y_val[:,1],  lat_val)
gb_test_err = geo_error_km(gb_test[:,0], gb_test[:,1], y_test[:,0], y_test[:,1], lat_test)

results['gbr_val']  = metrics(gb_val_err,  f"GradientBoosting (Val)")
results['gbr_test'] = metrics(gb_test_err, f"GradientBoosting (Test)")

joblib.dump(gbr_lat, 'models/baselines/gbr_lat.joblib')
joblib.dump(gbr_lon, 'models/baselines/gbr_lon.joblib')
print("  Saved GBR models.")

# ─── Save results ─────────────────────────────────────────────────────────────
with open('models/baselines/baseline_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nSaved: models/baselines/baseline_results.json")

# ─── Plot error distributions (val set) ───────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, errs, label, color in zip(
        axes,
        [p_val_err, r_val_err, gb_val_err],
        ['Persistence', 'Ridge Regression', 'Gradient Boosting'],
        ['steelblue', 'darkorange', 'forestgreen']):
    e = errs[~np.isnan(errs)]
    ax.hist(e, bins=40, color=color, alpha=0.75, edgecolor='black', linewidth=0.3)
    ax.axvline(np.mean(e),   color='red',   linestyle='--', linewidth=1.5, label=f'Mean: {np.mean(e):.1f} km')
    ax.axvline(np.median(e), color='black', linestyle=':',  linewidth=1.5, label=f'Median: {np.median(e):.1f} km')
    ax.set_title(label, fontsize=12)
    ax.set_xlabel('Geodesic Error (km)', fontsize=10)
    ax.set_ylabel('Count', fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

plt.suptitle('Baseline Model Error Distributions (Validation Set)', fontsize=13)
plt.tight_layout()
plt.savefig('models/baselines/baseline_error_distributions.png', dpi=150)
plt.close()
print("Saved: models/baselines/baseline_error_distributions.png")

# ─── Summary table ─────────────────────────────────────────────────────────────
print("\n=== VALIDATION SUMMARY TABLE ===")
print(f"{'Model':<25} {'Mean':>8} {'Median':>8} {'RMSE':>8} {'Max':>8}")
print("-" * 60)
for name, key in [('Persistence',        'persistence_val'),
                   ('Ridge Regression',   'ridge_val'),
                   ('Gradient Boosting',  'gbr_val')]:
    r = results[key]
    print(f"{name:<25} {r['mean_km']:>8.2f} {r['median_km']:>8.2f} {r['rmse_km']:>8.2f} {r['max_km']:>8.2f}")
print("\n(km)")

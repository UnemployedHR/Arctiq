"""
train_hybrid_model.py

Hybrid Physics + ML model for iceberg trajectory prediction.

Architecture:
  OpenBerg predicted displacement (physics baseline)
  + historical trajectory features
  → ML residual correction

  Hybrid prediction = physics_pred + residual_correction

For the physics baseline at scale, we cannot run OpenBerg for all
1215 icebergs (would require individual GLORYS/ERA5 downloads for each).
Instead, we implement a "physics-informed feature" approach:

  Physics features added to the ML model:
  - velocity from previous segment (a direct physics proxy)
  - elapsed time of forecast interval
  - estimated advection from previous speed and direction

This allows a physics-informed residual without requiring full OpenBerg runs.

For completeness, we also report iceberg 20857's actual OpenBerg error
as the physics baseline reference point.

The hybrid model is a GBR trained on:
  [all existing features] + [physics proxy: persistence forecast displacement]

Residual target = actual_displacement - persistence_forecast
"""

import os, sys, json, warnings, joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
os.makedirs('models/hybrid', exist_ok=True)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

R = 6371.0

def geo_error_km_full(pred_dlat, pred_dlon, true_dlat, true_dlon, lat_ref):
    pred_la = np.radians(lat_ref + pred_dlat)
    true_la = np.radians(lat_ref + true_dlat)
    dlo = np.radians(true_dlon - pred_dlon)
    dla = true_la - pred_la
    a = np.sin(dla/2)**2 + np.cos(pred_la)*np.cos(true_la)*np.sin(dlo/2)**2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def metrics_dict(errs, label):
    e = np.array(errs)
    e = e[~np.isnan(e)]
    print(f"  {label} (n={len(e)}):  mean={np.mean(e):.3f}  median={np.median(e):.3f}  "
          f"rmse={np.sqrt(np.mean(e**2)):.3f}  max={np.max(e):.3f}")
    return {
        'n': int(len(e)),
        'mean_km':   round(float(np.mean(e)),   3),
        'median_km': round(float(np.median(e)), 3),
        'rmse_km':   round(float(np.sqrt(np.mean(e**2))), 3),
        'min_km':    round(float(np.min(e)),    3),
        'max_km':    round(float(np.max(e)),    3),
    }

# ─── Load data ────────────────────────────────────────────────────────────────
ml = pd.read_parquet('data/ml/final_ml_dataset.parquet')
with open('data/ml/ml_dataset_config.json') as f:
    config = json.load(f)

feature_cols = config['feature_cols']
target_cols  = config['target_cols']

train = ml[ml['split'] == 'train'].reset_index(drop=True)
val   = ml[ml['split'] == 'val'].reset_index(drop=True)
test  = ml[ml['split'] == 'test'].reset_index(drop=True)

# ─── Compute physics proxy: scaled-persistence forecast ───────────────────────
# Physics prior: if iceberg velocity is constant, next displacement scales with
# the ratio of forecast_dt to prev_dt.
# phys_dlat = prev_delta_lat * (forecast_dt / prev_dt)
# phys_dlon = prev_delta_lon * (forecast_dt / prev_dt)

def add_physics_prior(df):
    df = df.copy()
    # Clip ratio to 1.0 — do not extrapolate beyond the previous interval length
    # (iceberg velocity is not expected to remain constant over longer intervals)
    dt_ratio = (df['forecast_dt_hours'] / df['prev_dt_hours'].clip(lower=0.1)).clip(upper=1.0)
    df['phys_dlat'] = df['prev_delta_lat'] * dt_ratio
    df['phys_dlon'] = df['prev_delta_lon'] * dt_ratio
    return df

train = add_physics_prior(train)
val   = add_physics_prior(val)
test  = add_physics_prior(test)

# Extended feature set: add physics prior features
hybrid_feature_cols = feature_cols + ['phys_dlat', 'phys_dlon']

X_train = train[hybrid_feature_cols].values.astype(np.float32)
X_val   = val[hybrid_feature_cols].values.astype(np.float32)
X_test  = test[hybrid_feature_cols].values.astype(np.float32)

y_train = train[target_cols].values.astype(np.float32)
y_val   = val[target_cols].values.astype(np.float32)
y_test  = test[target_cols].values.astype(np.float32)

lat_train = train['lat'].values
lat_val   = val['lat'].values
lat_test  = test['lat'].values

# Physics prior predictions (persistence scaled by time ratio)
phys_train = np.stack([train['phys_dlat'].values, train['phys_dlon'].values], axis=1)
phys_val   = np.stack([val['phys_dlat'].values,   val['phys_dlon'].values],   axis=1)
phys_test  = np.stack([test['phys_dlat'].values,  test['phys_dlon'].values],  axis=1)

# Residual = actual - physics_prior
res_train = y_train - phys_train
res_val   = y_val   - phys_val

print(f"Residual train stats:")
print(f"  dlat residual: mean={res_train[:,0].mean():.4f} std={res_train[:,0].std():.4f}")
print(f"  dlon residual: mean={res_train[:,1].mean():.4f} std={res_train[:,1].std():.4f}")

# ─── Fit scaler on train only ─────────────────────────────────────────────────
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc   = scaler.transform(X_val)
X_test_sc  = scaler.transform(X_test)
joblib.dump(scaler, 'models/hybrid/hybrid_scaler.joblib')

# ─── Train residual model ────────────────────────────────────────────────────
print("\nTraining hybrid residual model (GBR on physics residual)...")
gbr_res_lat = GradientBoostingRegressor(
    random_state=RANDOM_SEED, n_estimators=200,
    learning_rate=0.05, max_depth=4, subsample=0.8, min_samples_leaf=5
)
gbr_res_lon = GradientBoostingRegressor(
    random_state=RANDOM_SEED, n_estimators=200,
    learning_rate=0.05, max_depth=4, subsample=0.8, min_samples_leaf=5
)
gbr_res_lat.fit(X_train_sc, res_train[:, 0])
gbr_res_lon.fit(X_train_sc, res_train[:, 1])

joblib.dump(gbr_res_lat, 'models/hybrid/hybrid_gbr_lat.joblib')
joblib.dump(gbr_res_lon, 'models/hybrid/hybrid_gbr_lon.joblib')
print("  Residual models saved.")

# ─── Hybrid predictions ───────────────────────────────────────────────────────
def hybrid_predict(X_sc, phys):
    res_lat = gbr_res_lat.predict(X_sc)
    res_lon = gbr_res_lon.predict(X_sc)
    return np.stack([phys[:,0] + res_lat, phys[:,1] + res_lon], axis=1)

hyb_val  = hybrid_predict(X_val_sc,  phys_val)
hyb_test = hybrid_predict(X_test_sc, phys_test)

hyb_val_err  = geo_error_km_full(hyb_val[:,0],  hyb_val[:,1],  y_val[:,0],  y_val[:,1],  lat_val)
hyb_test_err = geo_error_km_full(hyb_test[:,0], hyb_test[:,1], y_test[:,0], y_test[:,1], lat_test)

results = {
    'hybrid_val':  metrics_dict(hyb_val_err,  "Hybrid Physics+ML (Val)"),
    'hybrid_test': metrics_dict(hyb_test_err, "Hybrid Physics+ML (Test)"),
}

# Also compare against plain physics prior
phys_val_err  = geo_error_km_full(phys_val[:,0],  phys_val[:,1],  y_val[:,0],  y_val[:,1],  lat_val)
phys_test_err = geo_error_km_full(phys_test[:,0], phys_test[:,1], y_test[:,0], y_test[:,1], lat_test)
results['physics_prior_val']  = metrics_dict(phys_val_err,  "Physics Prior (Val)")
results['physics_prior_test'] = metrics_dict(phys_test_err, "Physics Prior (Test)")

# ─── Plot ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, errs, label, color in [
        (axes[0], hyb_val_err,  'Hybrid Physics+ML (Val)',   'purple'),
        (axes[1], phys_val_err, 'Physics Prior (Val)',        'teal')]:
    e = errs[~np.isnan(errs)]
    ax.hist(e, bins=40, color=color, alpha=0.7, edgecolor='black', linewidth=0.3)
    ax.axvline(np.mean(e),   color='red',   linestyle='--', linewidth=1.5, label=f'Mean: {np.mean(e):.1f} km')
    ax.axvline(np.median(e), color='black', linestyle=':',  linewidth=1.5, label=f'Median: {np.median(e):.1f} km')
    ax.set_title(label, fontsize=11)
    ax.set_xlabel('Geodesic Error (km)')
    ax.set_ylabel('Count')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
plt.suptitle('Hybrid Model Error Distribution (Validation Set)', fontsize=13)
plt.tight_layout()
plt.savefig('models/hybrid/hybrid_error_distribution.png', dpi=150)
plt.close()
print("Saved: models/hybrid/hybrid_error_distribution.png")

# ─── Save config ─────────────────────────────────────────────────────────────
hybrid_config = {
    'random_seed': RANDOM_SEED,
    'architecture': 'PhysicsPrior + GBR residual correction',
    'physics_prior': 'scaled-persistence (prev_delta * forecast_dt/prev_dt)',
    'residual_model': 'GradientBoostingRegressor (n_estimators=200)',
    'feature_cols': hybrid_feature_cols,
    'target_cols': target_cols,
    'note_openberg': (
        'Full OpenBerg physics baseline requires individual GLORYS+ERA5 downloads '
        'for each iceberg. These are not available for the full dataset. '
        'Iceberg 20857 OpenBerg June 9 error: 30.01 km (Case A surface-only) is '
        'documented in FORCING_ATTRIBUTION_7DAY.md as a REFERENCE ONLY point.'
    ),
}
with open('models/hybrid/hybrid_config.json', 'w') as f:
    json.dump(hybrid_config, f, indent=2)
with open('models/hybrid/hybrid_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Saved: models/hybrid/hybrid_config.json")
print("Saved: models/hybrid/hybrid_results.json")

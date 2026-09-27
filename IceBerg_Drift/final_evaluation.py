"""
final_evaluation.py

Final held-out test set evaluation of all models.
Run ONLY after all models are trained and val selection is complete.

Models evaluated:
  0. Persistence baseline
  1. Ridge Regression
  2. Gradient Boosting
  3. GRU (if PyTorch available)
  4. OpenBerg physics baseline (reference from iceberg 20857 only)
  5. Hybrid Physics + ML

Generates:
  BASELINE_MODEL_REPORT.md
  GRU_MODEL_REPORT.md
  HYBRID_MODEL_REPORT.md
  PHYSICS_BASELINE_REPORT.md
  FINAL_TEST_EVALUATION.md
  figures/model_comparison.png
  figures/error_distributions_all.png
"""

import os, json, warnings, joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
os.makedirs('figures', exist_ok=True)

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

def metrics_dict(errs, label=''):
    e = np.array(errs, dtype=float)
    e = e[~np.isnan(e)]
    if len(e) == 0:
        return {'n': 0, 'mean_km': None, 'median_km': None, 'rmse_km': None, 'min_km': None, 'max_km': None}
    return {
        'n':         int(len(e)),
        'mean_km':   round(float(np.mean(e)),   2),
        'median_km': round(float(np.median(e)), 2),
        'rmse_km':   round(float(np.sqrt(np.mean(e**2))), 2),
        'min_km':    round(float(np.min(e)),    2),
        'max_km':    round(float(np.max(e)),    2),
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

# Load scalers
scaler = joblib.load('models/baselines/ridge_scaler.joblib')

X_train = scaler.transform(train[feature_cols].values.astype(np.float32))
X_val   = scaler.transform(val[feature_cols].values.astype(np.float32))
X_test  = scaler.transform(test[feature_cols].values.astype(np.float32))
y_test  = test[target_cols].values.astype(np.float32)
lat_test = test['lat'].values
y_val   = val[target_cols].values.astype(np.float32)
lat_val  = val['lat'].values
y_train = train[target_cols].values.astype(np.float32)

# Feature indices
pidx_lat = feature_cols.index('prev_delta_lat')
pidx_lon = feature_cols.index('prev_delta_lon')

all_results = {}

# ─── 0. Persistence ───────────────────────────────────────────────────────────
X_test_raw = test[feature_cols].values.astype(np.float32)
p_test = np.stack([X_test_raw[:, pidx_lat], X_test_raw[:, pidx_lon]], axis=1)
p_err  = geo_error_km_full(p_test[:,0], p_test[:,1], y_test[:,0], y_test[:,1], lat_test)
all_results['persistence'] = metrics_dict(p_err, 'Persistence')
print(f"Persistence:  mean={all_results['persistence']['mean_km']:.2f}  "
      f"median={all_results['persistence']['median_km']:.2f}  "
      f"rmse={all_results['persistence']['rmse_km']:.2f}")

# ─── 1. Ridge ─────────────────────────────────────────────────────────────────
ridge_lat = joblib.load('models/baselines/ridge_lat.joblib')
ridge_lon = joblib.load('models/baselines/ridge_lon.joblib')
r_test = np.stack([ridge_lat.predict(X_test), ridge_lon.predict(X_test)], axis=1)
r_err  = geo_error_km_full(r_test[:,0], r_test[:,1], y_test[:,0], y_test[:,1], lat_test)
all_results['ridge'] = metrics_dict(r_err, 'Ridge Regression')
print(f"Ridge:        mean={all_results['ridge']['mean_km']:.2f}  "
      f"median={all_results['ridge']['median_km']:.2f}  "
      f"rmse={all_results['ridge']['rmse_km']:.2f}")

# ─── 2. Gradient Boosting ─────────────────────────────────────────────────────
gbr_lat = joblib.load('models/baselines/gbr_lat.joblib')
gbr_lon = joblib.load('models/baselines/gbr_lon.joblib')
gb_test = np.stack([gbr_lat.predict(X_test), gbr_lon.predict(X_test)], axis=1)
gb_err  = geo_error_km_full(gb_test[:,0], gb_test[:,1], y_test[:,0], y_test[:,1], lat_test)
all_results['gradient_boosting'] = metrics_dict(gb_err, 'Gradient Boosting')
print(f"GradBoost:    mean={all_results['gradient_boosting']['mean_km']:.2f}  "
      f"median={all_results['gradient_boosting']['median_km']:.2f}  "
      f"rmse={all_results['gradient_boosting']['rmse_km']:.2f}")

# ─── 3. GRU ───────────────────────────────────────────────────────────────────
try:
    import torch, torch.nn as nn
    from sklearn.preprocessing import StandardScaler as SS
    torch.manual_seed(RANDOM_SEED)

    feat_sc = joblib.load('models/gru/feature_scaler.joblib')
    tgt_sc  = joblib.load('models/gru/target_scaler.joblib')

    class IcebergGRU(nn.Module):
        def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.2, output_size=2):
            super().__init__()
            self.gru = nn.GRU(input_size=input_size, hidden_size=hidden_size,
                              num_layers=num_layers, batch_first=True,
                              dropout=dropout if num_layers > 1 else 0.0)
            self.dropout = nn.Dropout(dropout)
            self.fc1 = nn.Linear(hidden_size, 64)
            self.fc2 = nn.Linear(64, output_size)
            self.act = nn.GELU()
        def forward(self, x):
            out, _ = self.gru(x)
            return self.fc2(self.act(self.fc1(self.dropout(out[:, -1, :]))))

    X_test_gru = feat_sc.transform(test[feature_cols].values.astype(np.float32))
    Xte_t = torch.from_numpy(X_test_gru[:, np.newaxis, :]).float()
    model = IcebergGRU(input_size=len(feature_cols))
    model.load_state_dict(torch.load('models/gru/best_model.pt', map_location='cpu', weights_only=True))
    model.eval()
    with torch.no_grad():
        gru_pred_sc = model(Xte_t).numpy()
    gru_pred = tgt_sc.inverse_transform(gru_pred_sc)
    gru_err  = geo_error_km_full(gru_pred[:,0], gru_pred[:,1], y_test[:,0], y_test[:,1], lat_test)
    all_results['gru'] = metrics_dict(gru_err, 'GRU')
    print(f"GRU:          mean={all_results['gru']['mean_km']:.2f}  "
          f"median={all_results['gru']['median_km']:.2f}  "
          f"rmse={all_results['gru']['rmse_km']:.2f}")
    GRU_AVAILABLE = True
except Exception as ex:
    print(f"GRU evaluation skipped: {ex}")
    all_results['gru'] = {'n': 0, 'mean_km': None, 'median_km': None, 'rmse_km': None,
                          'min_km': None, 'max_km': None, 'note': str(ex)}
    GRU_AVAILABLE = False
    gru_err = np.array([])

# ─── 4. OpenBerg physics reference ────────────────────────────────────────────
# Full OpenBerg runs require individual GLORYS+ERA5 downloads per iceberg.
# Reference point: iceberg 20857 (TRAIN split), June 9 endpoint.
OPENBERG_REF = {
    'iceberg': 20857,
    'split': 'train (reference only, not test)',
    'case': 'Surface-only (vertical_profile=False)',
    'period': '2021-06-02 to 2021-06-09',
    'error_km': 30.01,
    'iip_lat': 59.4050, 'iip_lon': -62.1150,
    'model_lat': 59.5212, 'model_lon': -62.5944,
    'note': 'Single-iceberg reference. Cannot generalise to population statistics.',
}
all_results['openberg_physics_ref'] = OPENBERG_REF
print(f"OpenBerg ref: single iceberg 20857, June 9 error = {OPENBERG_REF['error_km']} km (TRAIN split)")

# ─── 5. Hybrid ────────────────────────────────────────────────────────────────
try:
    hyb_sc  = joblib.load('models/hybrid/hybrid_scaler.joblib')
    hyb_lat = joblib.load('models/hybrid/hybrid_gbr_lat.joblib')
    hyb_lon = joblib.load('models/hybrid/hybrid_gbr_lon.joblib')

    test2 = test.copy()
    dt_ratio = (test2['forecast_dt_hours'] / test2['prev_dt_hours'].clip(lower=0.1)).clip(upper=1.0)
    test2['phys_dlat'] = test2['prev_delta_lat'] * dt_ratio
    test2['phys_dlon'] = test2['prev_delta_lon'] * dt_ratio
    hybrid_feature_cols = feature_cols + ['phys_dlat', 'phys_dlon']
    X_test_h = hyb_sc.transform(test2[hybrid_feature_cols].values.astype(np.float32))
    phys_test = np.stack([test2['phys_dlat'].values, test2['phys_dlon'].values], axis=1)
    hyb_pred  = np.stack([
        phys_test[:,0] + hyb_lat.predict(X_test_h),
        phys_test[:,1] + hyb_lon.predict(X_test_h),
    ], axis=1)
    hyb_err = geo_error_km_full(hyb_pred[:,0], hyb_pred[:,1], y_test[:,0], y_test[:,1], lat_test)
    all_results['hybrid'] = metrics_dict(hyb_err, 'Hybrid')
    print(f"Hybrid:       mean={all_results['hybrid']['mean_km']:.2f}  "
          f"median={all_results['hybrid']['median_km']:.2f}  "
          f"rmse={all_results['hybrid']['rmse_km']:.2f}")
    HYBRID_AVAILABLE = True
except Exception as ex:
    print(f"Hybrid evaluation skipped: {ex}")
    all_results['hybrid'] = {'n': 0, 'note': str(ex)}
    HYBRID_AVAILABLE = False
    hyb_err = np.array([])

# ─── Save results ─────────────────────────────────────────────────────────────
with open('models/final_test_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)
print("\nSaved: models/final_test_results.json")

# ─── Comparison bar plot ──────────────────────────────────────────────────────
model_labels = ['Persistence', 'Ridge\nRegression', 'Gradient\nBoosting']
mean_errs    = [all_results['persistence']['mean_km'],
                all_results['ridge']['mean_km'],
                all_results['gradient_boosting']['mean_km']]
median_errs  = [all_results['persistence']['median_km'],
                all_results['ridge']['median_km'],
                all_results['gradient_boosting']['median_km']]
rmse_errs    = [all_results['persistence']['rmse_km'],
                all_results['ridge']['rmse_km'],
                all_results['gradient_boosting']['rmse_km']]
colors = ['#4878d0', '#ee854a', '#6acc65']

if GRU_AVAILABLE:
    model_labels.append('GRU')
    mean_errs.append(all_results['gru']['mean_km'])
    median_errs.append(all_results['gru']['median_km'])
    rmse_errs.append(all_results['gru']['rmse_km'])
    colors.append('#d65f5f')

if HYBRID_AVAILABLE:
    model_labels.append('Hybrid\nPhysics+ML')
    mean_errs.append(all_results['hybrid']['mean_km'])
    median_errs.append(all_results['hybrid']['median_km'])
    rmse_errs.append(all_results['hybrid']['rmse_km'])
    colors.append('#956cb4')

x = np.arange(len(model_labels))
width = 0.27

fig, ax = plt.subplots(figsize=(12, 6))
bars1 = ax.bar(x - width, mean_errs,   width, label='Mean error (km)',   color=[c+'bb' for c in colors])
bars2 = ax.bar(x,         median_errs, width, label='Median error (km)', color=colors)
bars3 = ax.bar(x + width, rmse_errs,   width, label='RMSE (km)',         color=[c+'66' for c in colors])
ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('Geodesic Error (km)', fontsize=12)
ax.set_title('Model Comparison — Final Test Set Evaluation', fontsize=13)
ax.set_xticks(x)
ax.set_xticklabels(model_labels, fontsize=10)
ax.legend(fontsize=10)
ax.grid(True, axis='y', alpha=0.3)
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        h = bar.get_height()
        if h is not None:
            ax.text(bar.get_x() + bar.get_width()/2., h + 0.5, f'{h:.1f}', ha='center', va='bottom', fontsize=7)
plt.tight_layout()
plt.savefig('figures/model_comparison.png', dpi=150)
plt.close()
print("Saved: figures/model_comparison.png")

# ─── Error distributions all models ──────────────────────────────────────────
n_plots = 3 + int(GRU_AVAILABLE) + int(HYBRID_AVAILABLE)
fig, axes = plt.subplots(1, n_plots, figsize=(5*n_plots, 5))
err_sets = [
    (p_err,  'Persistence',          '#4878d0'),
    (r_err,  'Ridge Regression',     '#ee854a'),
    (gb_err, 'Gradient Boosting',    '#6acc65'),
]
if GRU_AVAILABLE:    err_sets.append((gru_err, 'GRU',              '#d65f5f'))
if HYBRID_AVAILABLE: err_sets.append((hyb_err, 'Hybrid Physics+ML','#956cb4'))

for ax, (err, label, color) in zip(axes, err_sets):
    e = err[~np.isnan(err)]
    e_capped = np.clip(e, 0, np.percentile(e, 95))  # cap at 95th pct for readability
    ax.hist(e_capped, bins=35, color=color, alpha=0.75, edgecolor='black', linewidth=0.3)
    ax.axvline(np.mean(e),   color='red',   linestyle='--', linewidth=1.5, label=f'Mean: {np.mean(e):.0f}km')
    ax.axvline(np.median(e), color='black', linestyle=':',  linewidth=1.5, label=f'Median: {np.median(e):.0f}km')
    ax.set_title(label, fontsize=10)
    ax.set_xlabel('Error (km, capped at 95th pctile)', fontsize=8)
    ax.set_ylabel('Count', fontsize=8)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

plt.suptitle('Error Distributions — Final Test Set', fontsize=12)
plt.tight_layout()
plt.savefig('figures/error_distributions_all.png', dpi=150)
plt.close()
print("Saved: figures/error_distributions_all.png")

print("\nFinal evaluation complete.")

"""
build_ml_dataset.py

Builds the final ML dataset from IIP trajectory segments.

ML problem definition:
  Given the CURRENT inter-observation displacement (and available features AT the
  previous observation), predict the NEXT inter-observation displacement.

Because IIP observations are highly irregular (median ~84h gap, range 0.1–740h),
we use the ACTUAL elapsed-time displacement (not a fixed horizon):

  Input features at observation i-1:
    - lat, lon
    - previous delta_lat, delta_lon (from i-2 → i-1)
    - previous displacement_km, bearing, speed_mps
    - dt_hours of previous interval
    - SIZE, SHAPE (categorical, one-hot encoded)
    - day-of-year cyclical
    - hour cyclical
    - dt_hours of prediction interval (time until next observation)

  Target:
    - delta_lat   (actual displacement northward to next obs)
    - delta_lon   (actual displacement eastward to next obs)

  Derived from target:
    - displacement_km, bearing_deg at evaluation time

Dataset construction:
  - Split by iceberg_number (no leakage)
  - Only include consecutive pairs with valid previous segment
  - Require >=3 observations per iceberg (so we have prev + current + next)

No environmental NetCDF interpolation is attempted here (would require
iceberg-specific GLORYS/ERA5 downloads for all 1215 icebergs, which are
not available). Environmental features are therefore left as NOT AVAILABLE
and flagged in the report.

PHASE 2 (environmental alignment) and PHASE 3 (final ML dataset) are
merged here as a practical combined step given the available data.
"""

import os, json, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')
os.makedirs('data/ml', exist_ok=True)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ─── Load data ────────────────────────────────────────────────────────────────
segs = pd.read_csv('data/iip/iip_trajectory_segments.csv', parse_dates=['t_ref', 't_next'])
train_ids = set(pd.read_csv('data/iip/ml_splits/train_icebergs.csv')['iceberg_number'])
val_ids   = set(pd.read_csv('data/iip/ml_splits/validation_icebergs.csv')['iceberg_number'])
test_ids  = set(pd.read_csv('data/iip/ml_splits/test_icebergs.csv')['iceberg_number'])

print(f"Segments loaded: {len(segs)}")
print(f"Split: train={len(train_ids)}, val={len(val_ids)}, test={len(test_ids)}")

# ─── SIZE/SHAPE encoding ──────────────────────────────────────────────────────
SIZE_MAP  = {'BB': 0, 'GR': 1, 'SM': 2, 'MED': 3, 'LG': 4, 'VLG': 5,
             'GEN': -1, 'NTB': -1, 'DD': -1, 'RAD': -1, 'PIN': -1,
             'WDG': -1, 'TAB': -1, 'DOM': -1, 'BLK': -1, 'ISL': -1}
SHAPE_MAP = {'BB': 0, 'GR': 1, 'SM': 2, 'MED': 3, 'LG': 4, 'VLG': 5,
             'GEN': -1, 'NTB': -1, 'DD': -1, 'RAD': -1, 'PIN': -1,
             'WDG': -1, 'TAB': -1, 'DOM': -1, 'BLK': -1, 'ISL': -1}

# Size/Shape are already valid strings; one-hot or ordinal:
# Use one-hot for SIZE (10 cats → 10 cols), SHAPE (8 cats → 8 cols)
SIZE_CATS  = sorted(segs['SIZE'].dropna().unique().tolist())
SHAPE_CATS = sorted(segs['SHAPE'].dropna().unique().tolist())

# ─── Cyclical time encoding ───────────────────────────────────────────────────
def cyclical(val, period):
    return np.sin(2 * np.pi * val / period), np.cos(2 * np.pi * val / period)

# ─── Build sample pairs ───────────────────────────────────────────────────────
# For iceberg i, pair segment j-1 (input context) with segment j (target)
# Require both segments to be consecutive (obs_index[j] = obs_index[j-1]+1)

rows = []
for num, g in segs.groupby('iceberg_number'):
    g = g.sort_values('obs_index').reset_index(drop=True)
    if len(g) < 2:
        continue
    for j in range(1, len(g)):
        prev = g.iloc[j-1]
        curr = g.iloc[j]
        # Must be consecutive observations
        if curr['obs_index'] != prev['obs_index'] + 1:
            continue
        # ── Input features from previous segment (j-1) ──
        t_ref = prev['t_ref']
        doy_sin, doy_cos = cyclical(t_ref.day_of_year, 365.25)
        hr_sin,  hr_cos  = cyclical(t_ref.hour, 24)

        size_oh  = {f'SIZE_{s}' : int(prev['SIZE'] == s)  for s in SIZE_CATS}
        shape_oh = {f'SHAPE_{s}': int(prev['SHAPE'] == s) for s in SHAPE_CATS}

        sample = {
            # Identifiers
            'iceberg_number'       : num,
            'split'                : ('train' if num in train_ids else
                                      'val'   if num in val_ids   else
                                      'test'  if num in test_ids  else 'unknown'),
            # Reference time
            't_ref'                : t_ref,
            't_next'               : curr['t_next'],
            # Position at t_ref
            'lat'                  : prev['lat'],
            'lon'                  : prev['lon'],
            # Previous segment features (context: what just happened)
            'prev_delta_lat'       : prev['delta_lat'],
            'prev_delta_lon'       : prev['delta_lon'],
            'prev_displacement_km' : prev['displacement_km'],
            'prev_speed_mps'       : prev['speed_mps'],
            'prev_bearing_sin'     : np.sin(np.radians(prev['bearing_deg'])),
            'prev_bearing_cos'     : np.cos(np.radians(prev['bearing_deg'])),
            'prev_dt_hours'        : prev['dt_hours'],
            # Forecast interval
            'forecast_dt_hours'    : curr['dt_hours'],
            # Time cyclical features
            'doy_sin'              : round(doy_sin, 6),
            'doy_cos'              : round(doy_cos, 6),
            'hr_sin'               : round(hr_sin, 6),
            'hr_cos'               : round(hr_cos, 6),
            # Categorical (one-hot)
            **size_oh,
            **shape_oh,
            # Targets
            'target_delta_lat'     : curr['delta_lat'],
            'target_delta_lon'     : curr['delta_lon'],
            'target_displacement_km': curr['displacement_km'],
            'target_bearing_deg'   : curr['bearing_deg'],
            'target_dt_hours'      : curr['dt_hours'],
        }
        rows.append(sample)

ml = pd.DataFrame(rows)
print(f"\nML samples (pairs): {len(ml)}")
print(f"Unique icebergs in ML: {ml['iceberg_number'].nunique()}")
print(f"\nSplit breakdown:")
print(ml['split'].value_counts())

# ─── Leakage verification ─────────────────────────────────────────────────────
train_ibs = set(ml[ml['split']=='train']['iceberg_number'])
val_ibs   = set(ml[ml['split']=='val']['iceberg_number'])
test_ibs  = set(ml[ml['split']=='test']['iceberg_number'])
assert len(train_ibs & val_ibs) == 0,  "LEAKAGE: train/val overlap"
assert len(train_ibs & test_ibs) == 0, "LEAKAGE: train/test overlap"
assert len(val_ibs   & test_ibs) == 0, "LEAKAGE: val/test overlap"
print("Leakage check: PASSED (no iceberg ID overlap between splits)")

# ─── Save ─────────────────────────────────────────────────────────────────────
ml.to_parquet('data/ml/final_ml_dataset.parquet', index=False)
ml.to_csv('data/ml/final_ml_dataset.csv', index=False)
print("Saved: data/ml/final_ml_dataset.parquet")
print("Saved: data/ml/final_ml_dataset.csv")

# ─── Feature list ─────────────────────────────────────────────────────────────
feature_cols = [
    'lat', 'lon',
    'prev_delta_lat', 'prev_delta_lon', 'prev_displacement_km',
    'prev_speed_mps', 'prev_bearing_sin', 'prev_bearing_cos', 'prev_dt_hours',
    'forecast_dt_hours',
    'doy_sin', 'doy_cos', 'hr_sin', 'hr_cos',
] + [f'SIZE_{s}' for s in SIZE_CATS] + [f'SHAPE_{s}' for s in SHAPE_CATS]

target_cols = ['target_delta_lat', 'target_delta_lon']

config = {
    'random_seed': RANDOM_SEED,
    'feature_cols': feature_cols,
    'target_cols': target_cols,
    'n_features': len(feature_cols),
    'n_targets': len(target_cols),
    'total_samples': len(ml),
    'train_samples': int((ml['split']=='train').sum()),
    'val_samples':   int((ml['split']=='val').sum()),
    'test_samples':  int((ml['split']=='test').sum()),
    'note_environmental': 'No environmental (GLORYS/ERA5) features: only iceberg-specific files downloaded for iceberg 20857. All other icebergs lack GLORYS/ERA5 coverage. Environmental features are UNAVAILABLE for the full ML dataset.',
}
with open('data/ml/ml_dataset_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print("Saved: data/ml/ml_dataset_config.json")

# ─── Summary stats ────────────────────────────────────────────────────────────
print("\nTarget distribution:")
print(ml[['target_delta_lat','target_delta_lon','target_displacement_km']].describe())
print("\nForecast dt_hours distribution:")
print(ml['forecast_dt_hours'].describe())
print("\nMissing values:")
print(ml[feature_cols + target_cols].isna().sum())

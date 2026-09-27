"""
STEP 3 — Merge ATL10 freeboard + GLORYS12 thickness → Train ML Model
Based on: Kern et al. (2016) methodology

Run this AFTER:
  - download.py      → data/atl10/ folder has .h5 files
  - download_glorys.py → data/glorys_sithick_2019_2025.nc exists
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
import h5py
import netCDF4 as nc
import xgboost as xgb

# Use non-interactive backend BEFORE importing pyplot (fixes Windows hang)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

def log(msg):
    print(msg, flush=True)
    sys.stdout.flush()

# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
RHO_WATER = 1023.9
RHO_ICE   = 915.1
RHO_SNOW  = 300.0

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD GLORYS12 THICKNESS GRID
# ══════════════════════════════════════════════════════════════════════════════
def load_glorys(nc_path="data/glorys_sithick_2019_2025.nc"):
    """
    Load GLORYS12 lazily — only metadata + time index.
    Returns dataset handle (kept open), lats, lons, date_index.
    Call close_glorys(ds) when done.
    """
    log(f"Loading GLORYS12 metadata from {nc_path} ...")
    ds = nc.Dataset(nc_path)

    lats  = ds.variables['latitude'][:]
    lons  = ds.variables['longitude'][:]
    times = nc.num2date(ds.variables['time'][:],
                        ds.variables['time'].units)

    log(f"  GLORYS grid: {len(lats)} lats x {len(lons)} lons x {len(times)} days")
    log(f"  Lat range: {lats.min():.1f} - {lats.max():.1f}")
    log(f"  Date range: {times[0]} - {times[-1]}")

    # Build month → list of time indices  (do NOT load sit array!)
    date_index = {}
    for i, t in enumerate(times):
        key = (t.year, t.month)
        if key not in date_index:
            date_index[key] = []
        date_index[key].append(i)

    # ds stays open so we can slice later
    return ds, lats, lons, date_index


def lookup_glorys_thickness(lat_arr, lon_arr, year_arr, month_arr,
                            ds, lats, lons, date_index):
    """
    Match each ATL10 point to nearest GLORYS cell.
    Loads one month of GLORYS at a time to stay within RAM.
    """
    thickness_labels = np.full(len(lat_arr), np.nan)

    # Group ATL10 points by (year, month) so we read each GLORYS month once
    ym_keys = set(zip(year_arr.astype(int), month_arr.astype(int)))
    log(f"  Unique year-month combos to process: {len(ym_keys)}")

    sit_var = ds.variables['sithick']   # lazy handle — no data loaded yet

    for ym_idx, (yr, mo) in enumerate(sorted(ym_keys)):
        key = (yr, mo)
        if key not in date_index:
            continue

        # Load only this month's daily slices  (~30 days × 301 × 4320 ≈ 300 MB)
        t_indices = date_index[key]
        monthly_sit = np.mean(sit_var[t_indices, :, :], axis=0)  # (lat, lon)

        # Find ATL10 points that belong to this month
        point_mask = (year_arr.astype(int) == yr) & (month_arr.astype(int) == mo)
        pts = np.where(point_mask)[0]

        if len(pts) == 0:
            continue

        for i in pts:
            lat_idx = np.argmin(np.abs(lats - lat_arr[i]))
            lon_idx = np.argmin(np.abs(lons - lon_arr[i]))
            val = monthly_sit[lat_idx, lon_idx]
            if not np.ma.is_masked(val) and val > 0:
                thickness_labels[i] = float(val)

        log(f"  [{ym_idx+1}/{len(ym_keys)}] {yr}-{mo:02d}: matched {(~np.isnan(thickness_labels[pts])).sum():,} / {len(pts):,} points")

    ds.close()
    return thickness_labels


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — READ ATL10 FILES
# ══════════════════════════════════════════════════════════════════════════════
FILL_VALUE = 1e10  # ATL10 fill value is ~3.4e38; anything above 1e10 is fill

def read_atl10_file(filepath, season, year):
    records = []
    beams = ['gt1l', 'gt1r', 'gt2l', 'gt2r', 'gt3l', 'gt3r']

    with h5py.File(filepath, 'r') as f:
        for beam in beams:
            seg = f"{beam}/freeboard_segment"
            if seg not in f:
                continue
            try:
                lat = f[f"{seg}/latitude"][:]
                lon = f[f"{seg}/longitude"][:]
                fb  = f[f"{seg}/beam_fb_height"][:]

                # Use beam_fb_unc as uncertainty (fb_sigma not available in ATL10-02)
                if f"{seg}/beam_fb_unc" in f:
                    fb_unc = f[f"{seg}/beam_fb_unc"][:]
                else:
                    fb_unc = np.zeros_like(fb)

                # Use quality flag if available (1=best, 4=poor)
                if f"{seg}/beam_fb_quality_flag" in f:
                    qflag = f[f"{seg}/beam_fb_quality_flag"][:]
                else:
                    qflag = np.ones_like(fb)

                # Remove fill values, keep valid freeboard range
                valid_fb  = (fb > 0.01) & (fb < 1.5) & (fb < FILL_VALUE)
                valid_unc = (fb_unc < 0.5) & (fb_unc < FILL_VALUE)
                valid_q   = (qflag <= 3)   # quality flag 1-3 acceptable

                mask = valid_fb & valid_unc & valid_q
                if mask.sum() == 0:
                    continue

                records.append(pd.DataFrame({
                    'lat':       lat[mask],
                    'lon':       lon[mask],
                    'freeboard': fb[mask],
                    'fb_sigma':  fb_unc[mask],
                    'sic':       np.full(mask.sum(), 80.0),  # placeholder; filter already applied
                    'beam':      beam,
                    'season':    season,
                    'year':      year,
                    'month':     6 if season == 'MJ' else (11 if season == 'ON' else 2),
                }))
            except KeyError as e:
                pass

    return pd.concat(records, ignore_index=True) if records else None


def load_all_atl10(data_dir="data/atl10"):
    all_files = glob.glob(f"{data_dir}/**/*.h5", recursive=True)
    all_files += glob.glob(f"{data_dir}/*.h5")
    all_files = list(set(all_files))
    log(f"Found {len(all_files)} ATL10 files")

    if not all_files:
        log("No ATL10 files found in data/atl10/")
        return None

    dfs = []
    for i, fp in enumerate(sorted(all_files)):
        parent = os.path.basename(os.path.dirname(fp))
        parts  = parent.split("_")
        season = parts[0] if len(parts) == 2 else "MJ"
        year   = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 2019
        log(f"  [{i+1}/{len(all_files)}] {os.path.basename(fp)} - {season} {year}")
        df = read_atl10_file(fp, season, year)
        if df is not None:
            dfs.append(df)

    return pd.concat(dfs, ignore_index=True) if dfs else None


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════
def assign_region(lon, lat):
    if (-60 <= lon <= -20) and (lat < -65): return 'WWS'
    elif (-20 <= lon <= 20) and (lat < -60): return 'EWeddell'
    elif (20 <= lon <= 90) and (lat < -60): return 'IndianOcean'
    elif (90 <= lon <= 160) and (lat < -60): return 'WPacific'
    elif (-130 <= lon <= -60) and (lat < -70): return 'Ross'
    elif (-180 <= lon <= -130) and (lat < -60): return 'EPacific'
    else: return 'Other'

def build_features(df):
    df['region']  = df.apply(lambda r: assign_region(r['lon'], r['lat']), axis=1)
    df['lat_abs'] = df['lat'].abs()
    df['lat_bin'] = pd.cut(df['lat_abs'], bins=[55,65,70,75,80,90],
                           labels=[1,2,3,4,5]).astype(int)

    season_offsets = {'MJ': 0.06, 'ON': 0.09, 'FM': 0.04}
    df['snow_depth_est'] = df.apply(
        lambda r: 0.12 * r['freeboard'] + season_offsets.get(r['season'], 0.05), axis=1)

    df['year_norm']   = (df['year'] - 2019) / 7.0
    season_map        = {'MJ': 0, 'ON': 1, 'FM': 2}
    df['season_code'] = df['season'].map(season_map).fillna(0).astype(int)

    le = LabelEncoder()
    df['region_code'] = le.fit_transform(df['region'])
    return df, le


FEATURE_COLS = [
    'freeboard', 'fb_sigma', 'snow_depth_est', 'sic',
    'region_code', 'season_code', 'lat_abs', 'lat_bin', 'year_norm'
]

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — TRAIN
# ══════════════════════════════════════════════════════════════════════════════
def train_model(df, label_col='thickness_glorys'):
    log(f"\n-- Training XGBoost on {len(df):,} real samples --")
    X = df[FEATURE_COLS].values
    y = df[label_col].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=600,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        objective='reg:squarederror',
        random_state=42,
        verbosity=0,
        early_stopping_rounds=50,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    mae    = mean_absolute_error(y_test, y_pred)
    r2     = r2_score(y_test, y_pred)
    log(f"  MAE = {mae:.3f} m")
    log(f"  R2  = {r2:.3f}")

    model.save_model("ice_density_model_REAL.json")
    log("  Model saved: ice_density_model_REAL.json")

    return model, X_test, y_test, y_pred


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    log("=" * 60)
    log("  ICE DENSITY MODEL - REAL DATA TRAINING")
    log("  ATL10 (2019-2026) + GLORYS12 labels")
    log("=" * 60)

    # 1. Load ATL10
    df = load_all_atl10("data/atl10")
    if df is None:
        log("No ATL10 data. Exiting.")
        sys.exit(1)
    log(f"\nATL10 loaded: {len(df):,} measurements")

    # 2. Load GLORYS
    glorys_path = "data/glorys_sithick_2019_2025.nc"
    if not os.path.exists(glorys_path):
        glorys_path = "glorys_sithick_2019_2025.nc"

    if not os.path.exists(glorys_path):
        log(f"GLORYS file not found at: {glorys_path}")
        sys.exit(1)

    ds_glorys, lats, lons, date_index = load_glorys(glorys_path)

    # 3. Match (reads GLORYS one month at a time — RAM-safe)
    log("\nMatching ATL10 freeboard -> GLORYS thickness labels ...")
    log("(Reads GLORYS month-by-month to stay within RAM)")

    df['thickness_glorys'] = lookup_glorys_thickness(
        df['lat'].values, df['lon'].values,
        df['year'].values, df['month'].values,
        ds_glorys, lats, lons, date_index
    )

    before = len(df)
    df = df.dropna(subset=['thickness_glorys'])
    df = df[df['thickness_glorys'] > 0.05]
    log(f"  Matched {len(df):,} / {before:,} points ({100*len(df)/before:.1f}%)")

    if len(df) < 100:
        log("Too few matched points. Check file paths.")
        sys.exit(1)

    # Sub-sample to 2M rows — XGBoost does not need 66M rows, 2M gives same accuracy
    MAX_SAMPLES = 2_000_000
    if len(df) > MAX_SAMPLES:
        log(f"\nSub-sampling {MAX_SAMPLES:,} rows from {len(df):,} (stratified by season+year) ...")
        df = df.groupby(['season', 'year'], group_keys=False).apply(
            lambda x: x.sample(min(len(x), int(MAX_SAMPLES * len(x) / len(df))), random_state=42)
        ).reset_index(drop=True)
        # Top up to exactly MAX_SAMPLES if needed
        if len(df) < MAX_SAMPLES:
            pass  # close enough
        log(f"  Sample size: {len(df):,} rows")

    # 4. Feature engineering
    df, le_region = build_features(df)
    log(f"\nFeature matrix ready: {len(df):,} samples x {len(FEATURE_COLS)} features")
    log(f"Thickness range: {df['thickness_glorys'].min():.2f} - {df['thickness_glorys'].max():.2f} m")

    # 5. Train
    model, X_test, y_true, y_pred = train_model(df)

    # 6. Plot (saved as PNG, no GUI popup)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Ice Density Model - REAL DATA (ATL10 + GLORYS12)', fontweight='bold')

    ax = axes[0]
    ax.scatter(y_true, y_pred, alpha=0.3, s=8, color='steelblue')
    lim = [0, max(y_true.max(), y_pred.max())]
    ax.plot(lim, lim, 'r--', lw=1.5)
    ax.set_xlabel('GLORYS Thickness (m)')
    ax.set_ylabel('Predicted Thickness (m)')
    ax.set_title(f'MAE={mean_absolute_error(y_true,y_pred):.3f}m  R2={r2_score(y_true,y_pred):.3f}')

    ax = axes[1]
    fi  = model.feature_importances_
    idx = np.argsort(fi)[::-1]
    ax.barh([FEATURE_COLS[i] for i in idx], fi[idx], color='teal')
    ax.set_title('Feature Importance')

    plt.tight_layout()
    plt.savefig('model_REAL_results.png', dpi=150, bbox_inches='tight')
    plt.close()
    log("\nPlot saved: model_REAL_results.png")

    # 7. Year trend
    log("\n-- Mean predicted thickness by year (Winter MJ) --")
    for yr in sorted(df['year'].unique()):
        sub = df[(df['year'] == yr) & (df['season'] == 'MJ')]
        if len(sub) > 0:
            pred = model.predict(sub[FEATURE_COLS].values)
            log(f"  {yr}: {pred.mean():.3f} m  (n={len(sub):,})")

    log("\nReal data training complete!")
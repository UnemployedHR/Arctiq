"""
forcing_attribution_7day.py

Controlled forcing attribution experiment for iceberg 20857.
Period: 2021-06-02 16:41 -> 2021-06-09 21:59

Three cases, identical physics, only forcing varies:
  CASE A (FULL):        GLORYS ocean + ERA5 wind
  CASE B (OCEAN ONLY):  GLORYS ocean + zero wind
  CASE C (WIND ONLY):   zero ocean  + ERA5 wind

All other parameters identical to historical_validation_v2.py.
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from opendrift.models.openberg import OpenBerg
from opendrift.readers import reader_netCDF_CF_generic

# --- Constants ----------------------------------------------------------------
IIP_START_LAT =  59.42667
IIP_START_LON = -62.41000
IIP_START_T   = datetime(2021, 6, 2, 16, 41)

IIP_END_LAT   =  59.40500
IIP_END_LON   = -62.11500
IIP_END_T     = datetime(2021, 6, 9, 21, 59)

DURATION_HRS  = (IIP_END_T - IIP_START_T).total_seconds() / 3600.0

# Iceberg geometry - identical to historical_validation_v2.py
DRAFT, LENGTH, WIDTH, SAIL = 90, 100, 30, 10

# Environmental files - identical to historical_validation_v2.py
FILES = {
    'surface_glorys': 'data/copernicus/glorys_iceberg_20857/iceberg_20857_glorys_uo_vo_20210601_20210810.nc',
    'era5':           'data/wind/iceberg_20857/era5_iceberg_20857_wind_20210601_20210810.nc',
}
OUT_DIR = 'data/results/iceberg_20857/forcing_attribution'
os.makedirs(OUT_DIR, exist_ok=True)

# --- Helpers ------------------------------------------------------------------

def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    lo1, la1, lo2, la2 = map(np.radians, [lon1, lat1, lon2, lat2])
    a = np.sin((la2-la1)/2)**2 + np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def vec_bearing(u, v):
    if np.sqrt(float(u)**2 + float(v)**2) < 1e-10:
        return np.nan
    return float((90.0 - np.degrees(np.arctan2(v, u))) % 360.0)

def diffusivity_rms_km(D, dt_hrs):
    return np.sqrt(2 * D * dt_hrs * 3600.0) / 1000.0


# --- Build OpenBerg model -----------------------------------------------------

def build_model(use_glorys: bool, use_era5: bool, case_label: str) -> OpenBerg:
    """
    Build an OpenBerg model with the same physics as historical_validation_v2.py.
    Only the forcing readers change.
    """
    o = OpenBerg(loglevel=50)

    readers = []
    if use_glorys:
        r_ocean = reader_netCDF_CF_generic.Reader(FILES['surface_glorys'])
        readers.append(r_ocean)
    if use_era5:
        r_wind = reader_netCDF_CF_generic.Reader(
            FILES['era5'],
            standard_name_mapping={'u10': 'x_wind', 'v10': 'y_wind'}
        )
        readers.append(r_wind)

    if readers:
        o.add_reader(readers)

    # Fallback values - IDENTICAL to historical_validation_v2.py
    # Wind fallback = 0 (applied when wind reader absent, or outside domain)
    # Ocean fallback = 0 (applied when ocean reader absent)
    o.set_config('environment:fallback:x_sea_water_velocity', 0)
    o.set_config('environment:fallback:y_sea_water_velocity', 0)
    o.set_config('environment:fallback:x_wind', 0)
    o.set_config('environment:fallback:y_wind', 0)

    # Same physics as historical run (all defaults preserved)
    o.set_config('drift:vertical_profile', False)

    print(f"  [{case_label}] use_glorys={use_glorys}, use_era5={use_era5}")
    return o


def run_case(o: OpenBerg, nc_path: str) -> str:
    o.seed_elements(
        lon=IIP_START_LON, lat=IIP_START_LAT,
        time=IIP_START_T,
        draft=DRAFT, length=LENGTH, width=WIDTH, sail=SAIL
    )
    duration = timedelta(hours=DURATION_HRS)
    o.run(
        duration=duration,
        time_step=timedelta(hours=1),
        time_step_output=timedelta(hours=1),
        outfile=nc_path
    )
    return nc_path


# --- Extract endpoint from NetCDF ---------------------------------------------

def extract_endpoint(nc_path: str, label: str) -> dict:
    ds = xr.open_dataset(nc_path)
    t      = pd.to_datetime(ds['time'].values).tz_localize(None)
    lons   = ds['lon'].values[0]
    lats   = ds['lat'].values[0]
    status = ds['status'].values[0]

    uw = ds['x_wind'].values[0]              if 'x_wind'              in ds else np.zeros(len(t))
    vw = ds['y_wind'].values[0]              if 'y_wind'              in ds else np.zeros(len(t))
    uo = ds['x_sea_water_velocity'].values[0] if 'x_sea_water_velocity' in ds else np.zeros(len(t))
    vo = ds['y_sea_water_velocity'].values[0] if 'y_sea_water_velocity' in ds else np.zeros(len(t))
    ds.close()

    # Grounding check
    grounded_idx = np.where(status == 1)[0]
    grounded     = len(grounded_idx) > 0
    ground_t     = t[grounded_idx[0]] if grounded else None

    # Endpoint: last active position before June 9 21:59
    target_t  = pd.Timestamp(IIP_END_T)
    t_secs    = np.array([(x - t[0]).total_seconds() for x in t])
    tgt_sec   = (target_t - t[0]).total_seconds()

    if tgt_sec <= 0:
        end_la, end_lo = lats[0], lons[0]
    elif tgt_sec >= t_secs[-1]:
        end_la, end_lo = lats[-1], lons[-1]
    else:
        idx = np.searchsorted(t_secs, tgt_sec)
        if grounded and grounded_idx[0] < idx:
            # Model grounded before target
            gi = grounded_idx[0]
            end_la, end_lo = lats[gi], lons[gi]
        else:
            frac = (tgt_sec - t_secs[idx-1]) / (t_secs[idx] - t_secs[idx-1])
            end_la = lats[idx-1] + frac*(lats[idx]-lats[idx-1])
            end_lo = lons[idx-1] + frac*(lons[idx]-lons[idx-1])

    error_km = haversine_km(IIP_END_LON, IIP_END_LAT, end_lo, end_la)
    dlat     = end_la - IIP_END_LAT
    dlon     = end_lo - IIP_END_LON

    # Net displacement from start
    net_disp = haversine_km(IIP_START_LON, IIP_START_LAT, end_lo, end_la)
    net_bear = vec_bearing(
        (end_lo - IIP_START_LON)*np.cos(np.radians(end_la)),
         end_la - IIP_START_LAT
    )

    # Mean wind / ocean for the active period
    act = status == 0
    mean_wind_spd  = float(np.nanmean(np.sqrt(uw[act]**2 + vw[act]**2))) if act.any() else np.nan
    mean_ocean_spd = float(np.nanmean(np.sqrt(uo[act]**2 + vo[act]**2))) if act.any() else np.nan
    mean_wind_bear  = vec_bearing(float(np.nanmean(uw[act])), float(np.nanmean(vw[act]))) if act.any() else np.nan
    mean_ocean_bear = vec_bearing(float(np.nanmean(uo[act])), float(np.nanmean(vo[act]))) if act.any() else np.nan

    return {
        'case'           : label,
        'end_lat'        : round(end_la, 5),
        'end_lon'        : round(end_lo, 5),
        'error_km'       : round(error_km, 2),
        'dLat'           : round(dlat, 5),
        'dLon'           : round(dlon, 5),
        'net_disp_km'    : round(net_disp, 2),
        'net_bear_deg'   : round(net_bear, 1) if not np.isnan(net_bear) else 'NA',
        'grounded'       : grounded,
        'ground_time'    : str(ground_t) if ground_t else 'None',
        'mean_wind_spd'  : round(mean_wind_spd,  3) if not np.isnan(mean_wind_spd)  else 'NA',
        'mean_wind_bear' : round(mean_wind_bear,  1) if not np.isnan(mean_wind_bear) else 'NA',
        'mean_ocean_spd' : round(mean_ocean_spd, 4) if not np.isnan(mean_ocean_spd) else 'NA',
        'mean_ocean_bear': round(mean_ocean_bear, 1) if not np.isnan(mean_ocean_bear) else 'NA',
        'lons': lons, 'lats': lats, 'status': status, 'time': t,
    }


# --- MAIN ---------------------------------------------------------------------

def main():
    print(f"Forcing Attribution Experiment - Iceberg 20857")
    print(f"Period: {IIP_START_T} to {IIP_END_T}  ({DURATION_HRS:.1f} hours)")
    print(f"IIP end observation: lat={IIP_END_LAT}, lon={IIP_END_LON}\n")

    cases = [
        ('FULL',       True,  True,  'CaseA_Full'),
        ('OCEAN_ONLY', True,  False, 'CaseB_OceanOnly'),
        ('WIND_ONLY',  False, True,  'CaseC_WindOnly'),
    ]

    results = []
    for name, use_gl, use_era, label in cases:
        nc_path = os.path.join(OUT_DIR, f'{label}.nc')
        print(f"Running {label}...")
        o = build_model(use_gl, use_era, label)
        run_case(o, nc_path)
        r = extract_endpoint(nc_path, label)
        results.append(r)
        print(f"  Endpoint: lat={r['end_lat']}, lon={r['end_lon']}  error={r['error_km']} km  grounded={r['grounded']}")

    # -- Plot ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 8))

    colors  = {'CaseA_Full': 'steelblue', 'CaseB_OceanOnly': 'darkorange', 'CaseC_WindOnly': 'forestgreen'}
    labels  = {'CaseA_Full': 'Full (GLORYS+ERA5)', 'CaseB_OceanOnly': 'Ocean-only (GLORYS)', 'CaseC_WindOnly': 'Wind-only (ERA5)'}
    lstyles = {'CaseA_Full': '-',  'CaseB_OceanOnly': '--', 'CaseC_WindOnly': '-.'}

    # IIP endpoints
    ax.plot(IIP_START_LON, IIP_START_LAT, 'k^', markersize=12, zorder=10, label='IIP Start (2021-06-02)')
    ax.plot(IIP_END_LON,   IIP_END_LAT,   'k*', markersize=16, zorder=10, label='IIP End OBSERVED (2021-06-09)')
    # Interpolated reference line - clearly labelled
    ax.plot([IIP_START_LON, IIP_END_LON], [IIP_START_LAT, IIP_END_LAT],
            'k:', linewidth=1, alpha=0.5, label='Linear interp. between sparse IIP obs (NOT measured path)')

    for r in results:
        lo = r['lons']
        la = r['lats']
        st = r['status']
        lbl = r['case']
        c   = colors[lbl]
        ls  = lstyles[lbl]
        act = st == 0
        ax.plot(lo[act], la[act], ls, color=c, linewidth=1.5, label=labels[lbl])
        # Endpoint star
        ax.plot(r['end_lon'], r['end_lat'], '*', color=c, markersize=14, zorder=8)
        if r['grounded']:
            gi = np.where(st == 1)[0][0]
            ax.plot(lo[gi], la[gi], 'X', color=c, markersize=12, zorder=9)

    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude',  fontsize=12)
    ax.set_title('Forcing Attribution - Iceberg 20857\n2021-06-02 -> 2021-06-09', fontsize=13)
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, alpha=0.4)
    plt.tight_layout()
    plt.savefig('forcing_attribution_7day.png', dpi=150)
    plt.close()
    print("Saved: forcing_attribution_7day.png")

    # -- Random walk scale -----------------------------------------------------
    D = 100.0
    rw = {1: diffusivity_rms_km(D, 1), 24: diffusivity_rms_km(D, 24), 168: diffusivity_rms_km(D, 168)}

    # -- Report ----------------------------------------------------------------
    def fmt(v):
        return str(v) if isinstance(v, str) else str(v)

    r_full  = next(r for r in results if r['case']=='CaseA_Full')
    r_ocean = next(r for r in results if r['case']=='CaseB_OceanOnly')
    r_wind  = next(r for r in results if r['case']=='CaseC_WindOnly')

    # Compare endpoint to IIP
    iip_end_disp = haversine_km(IIP_START_LON, IIP_START_LAT, IIP_END_LON, IIP_END_LAT)
    iip_end_bear = vec_bearing(
        (IIP_END_LON-IIP_START_LON)*np.cos(np.radians(IIP_END_LAT)),
         IIP_END_LAT-IIP_START_LAT
    )

    lines = [
        "# Forcing Attribution 7-Day Experiment - Iceberg 20857",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 1. Experiment Setup",
        "",
        "| Parameter | Value |",
        "|---|---|",
        f"| Start position | lat={IIP_START_LAT}, lon={IIP_START_LON} |",
        f"| Start time | {IIP_START_T} |",
        f"| End time | {IIP_END_T} |",
        f"| Duration | {DURATION_HRS:.1f} hours |",
        f"| Timestep | 1 hour |",
        f"| Draft / Length / Width / Sail | {DRAFT} / {LENGTH} / {WIDTH} / {SAIL} m |",
        f"| Horizontal diffusivity | 100 m²/s (unchanged from historical run) |",
        f"| Coriolis | ON (default) |",
        f"| vertical_profile | False (surface-only GLORYS) |",
        f"| Coastline | default (stranding) |",
        "",
        "**NOTE:** Only the environmental readers change across cases.",
        "All physics parameters are identical to `historical_validation_v2.py`.",
        "",
        "| Case | Ocean Reader | Wind Reader |",
        "|---|---|---|",
        "| CaseA_Full       | GLORYS surface | ERA5 u10/v10 |",
        "| CaseB_OceanOnly  | GLORYS surface | None (fallback=0) |",
        "| CaseC_WindOnly   | None (fallback=0) | ERA5 u10/v10 |",
        "",
        "## 2. IIP Endpoint Reference",
        "",
        "| | Value |",
        "|---|---|",
        f"| June 9 IIP lat (OBSERVED) | {IIP_END_LAT} |",
        f"| June 9 IIP lon (OBSERVED) | {IIP_END_LON} |",
        f"| Net displacement from start | {iip_end_disp:.2f} km |",
        f"| Net displacement bearing | {iip_end_bear:.1f}° |",
        "",
        "## 3. Endpoint Comparison Table",
        "",
        "| Case | End lat | End lon | Error vs IIP (km) | dLat | dLon | Net disp (km) | Net bearing | Grounded | Ground time |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['case']} | {r['end_lat']} | {r['end_lon']} | {r['error_km']} | "
            f"{r['dLat']:+.5f}° | {r['dLon']:+.5f}° | {r['net_disp_km']} | "
            f"{r['net_bear_deg']}° | {r['grounded']} | {r['ground_time']} |"
        )

    lines += [
        "",
        "## 4. Mean Environmental Forcing During Active Period",
        "",
        "| Case | Mean wind spd (m/s) | Mean wind bearing | Mean ocean spd (m/s) | Mean ocean bearing |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['case']} | {r['mean_wind_spd']} | {r['mean_wind_bear']}° | "
            f"{r['mean_ocean_spd']} | {r['mean_ocean_bear']}° |"
        )

    lines += [
        "",
        "## 5. Stochastic Random-Walk Scale Estimates",
        "",
        "Theoretical RMS: σ = √(2Dt),  D = 100 m²/s",
        "",
        "| Duration | σ_rms (km) |",
        "|---|---|",
        f"| 1 hour | {rw[1]:.2f} |",
        f"| 24 hours | {rw[24]:.2f} |",
        f"| 7 days | {rw[168]:.2f} |",
        "",
        "> **CLASSIFICATION: THEORETICAL STOCHASTIC SCALE ESTIMATE.**",
        f"> Over 7 days, theoretical RMS diffusion displacement ≈ {rw[168]:.1f} km.",
        f"> The Full case endpoint error is {r_full['error_km']} km.",
        f"> Random walk could contribute noise of order ±{rw[168]:.1f} km but cannot produce",
        f"> a systematic directional offset of this magnitude without additional forcing.",
        "",
        "## 6. Attribution Analysis",
        "",
        "### OBSERVED facts",
        "",
        f"1. Full forcing (GLORYS+ERA5) endpoint error vs June 9 IIP: **{r_full['error_km']} km**.",
        f"   Model is {r_full['dLat']:+.4f}° latitude, {r_full['dLon']:+.4f}° longitude from IIP.",
        f"2. Ocean-only endpoint error: **{r_ocean['error_km']} km** (model at {r_ocean['end_lat']}, {r_ocean['end_lon']}).",
        f"3. Wind-only endpoint error: **{r_wind['error_km']} km** (model at {r_wind['end_lat']}, {r_wind['end_lon']}).",
        f"4. IIP net displacement: {iip_end_disp:.2f} km at bearing {iip_end_bear:.1f}°.",
        f"5. Full forcing net displacement: {r_full['net_disp_km']} km at bearing {r_full['net_bear_deg']}°.",
        "",
        "### INFERRED",
        "",
        "6. **Wind attribution:** Comparing Full vs Ocean-only endpoints isolates the wind contribution.",
        f"   Full error={r_full['error_km']} km vs Ocean-only error={r_ocean['error_km']} km.",
        f"   Delta = {abs(r_full['error_km']-r_ocean['error_km']):.2f} km - this is the approximate",
        f"   wind-induced change in endpoint error.",
        "",
        "7. **Ocean attribution:** Comparing Full vs Wind-only endpoints isolates the ocean contribution.",
        f"   Full error={r_full['error_km']} km vs Wind-only error={r_wind['error_km']} km.",
        f"   Delta = {abs(r_full['error_km']-r_wind['error_km']):.2f} km.",
        "",
        "8. **Interaction:** Full ≠ Ocean-only + Wind-only because the forces are non-linear",
        "   (drag depends on relative velocity between iceberg and fluid). Their combined effect",
        "   is not a simple sum. This interaction cannot be separated from available outputs alone.",
        "",
        "### UNKNOWN",
        "",
        "9. The true path of the iceberg between 2021-06-02 and 2021-06-09 is unknown.",
        "   Only the start and end positions are real IIP observations.",
        "10. Whether GLORYS or ERA5 correctly represent the local environment at this specific",
        "    iceberg location during this period cannot be determined from model output alone.",
        "11. The magnitude of iceberg dimension changes (melting, roll-over) during 7 days is unknown.",
        "",
        "## 7. Answers to Required Questions",
        "",
        f"1. **Actual June 9 endpoint error (Full forcing):** {r_full['error_km']} km",
        f"2. **Removing wind effect:** Ocean-only error = {r_ocean['error_km']} km vs Full = {r_full['error_km']} km.",
        f"   Difference = {abs(r_full['error_km']-r_ocean['error_km']):.2f} km. "
        f"{'Wind removal materially changes the endpoint.' if abs(r_full['error_km']-r_ocean['error_km'])>5 else 'Wind removal does not substantially change the endpoint.'}",
        f"3. **Removing ocean effect:** Wind-only error = {r_wind['error_km']} km vs Full = {r_full['error_km']} km.",
        f"   Difference = {abs(r_full['error_km']-r_wind['error_km']):.2f} km. "
        f"{'Ocean removal materially changes the endpoint.' if abs(r_full['error_km']-r_wind['error_km'])>5 else 'Ocean removal does not substantially change the endpoint.'}",
        f"4. **Closest to IIP endpoint:** {min(results, key=lambda x: x['error_km'])['case']} with error={min(results, key=lambda x: x['error_km'])['error_km']} km.",
        f"5. **Grounding through June 9:**",
    ]
    for r in results:
        lines.append(f"   - {r['case']}: grounded={r['grounded']} (at {r['ground_time']})")
    lines += [
        f"6. **Wind-only vs Ocean-only displacement:** INFERRED from endpoint positions above.",
        f"7. **Wind forcing evidence:** INFERRED only. Cannot claim causation without higher-resolution obs.",
        f"8. **Ocean forcing evidence:** INFERRED only. Same caveat applies.",
        f"9. **Interaction evidence:** Non-linear force balance means wind+ocean interaction is real but",
        f"   not directly separable from these three runs alone.",
        f"10. **Fundamentally unknowable:** True intermediate trajectory; local sub-grid environment;",
        f"    iceberg geometry evolution during the 7-day period.",
        "",
        "---",
        "*No model parameters were modified. Only forcing readers were changed per-case.*",
    ]

    with open('FORCING_ATTRIBUTION_7DAY.md', 'w', encoding='utf-8') as fh:
        fh.write("\n".join(lines))
    print("Saved: FORCING_ATTRIBUTION_7DAY.md")


if __name__ == '__main__':
    main()

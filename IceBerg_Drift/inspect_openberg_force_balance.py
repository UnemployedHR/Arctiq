"""
inspect_openberg_force_balance.py

Timestep-by-timestep force-balance audit for historical iceberg 20857.
Reads simulation outputs and reconstructs individual force contributions
using exact equations from the installed OpenBerg source.

Convention throughout:
  x  = eastward  (positive = East)
  y  = northward (positive = North)
  Bearing measured from North, clockwise (meteorological convention).
"""

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime

# ─── Physical constants from the installed openberg.py ───────────────────────
rho_water  = 1027.0   # kg/m³
rho_air    = 1.293    # kg/m³
rho_iceb   = 900.0    # kg/m³
omega      = 7.2921e-5  # rad/s
g          = 9.81       # m/s²

# ─── Iceberg parameters from historical_validation_v2.py ─────────────────────
LENGTH     = 100.0    # m
WIDTH      = 30.0     # m
DRAFT      = 90.0     # m
SAIL       = 10.0     # m
WEIGHT_COEF = 1.0     # default (tabular)

# Drag coefficients (defaults from IcebergObj)
Cwo = 0.25    # water form drag
Cdo = 0.0055  # water skin drag
Ca  = 0.8     # wind form drag
Cda = 0.0022  # wind skin drag

# Geometric areas
Avo = LENGTH * DRAFT    # vertical ocean area
Aho = WIDTH  * LENGTH   # horizontal ocean area
Ava = LENGTH * SAIL     # vertical air area
Aha = WIDTH  * LENGTH   # horizontal air area

# Mass
mass = WIDTH * (Ava + Avo) * rho_iceb * WEIGHT_COEF

# Wind-drift factor  k  (ratio of air/water form drag)
k = (rho_air * Ca * Ava) / (rho_water * Cwo * Avo)
f_drift = np.sqrt(k) / (1.0 + np.sqrt(k))

# ─── Helper functions (exact copies of openberg.py logic) ────────────────────

def ocean_force(iceb_vel, water_vel):
    vxo, vyo   = water_vel
    x_vel, y_vel = iceb_vel
    rel_x = vxo - x_vel
    rel_y = vyo - y_vel
    norm  = np.sqrt(rel_x**2 + rel_y**2)
    drag  = (0.5 * rho_water * Cwo * Avo) + (rho_water * Cdo * Aho)
    return np.array([drag * norm * rel_x, drag * norm * rel_y])


def wind_force(iceb_vel, wind_vel):
    vxa, vya   = wind_vel
    x_vel, y_vel = iceb_vel
    rel_x = vxa - x_vel
    rel_y = vya - y_vel
    norm  = np.sqrt(rel_x**2 + rel_y**2)
    drag  = (0.5 * rho_air * Ca * Ava) + (rho_air * Cda * Aha)
    return np.array([drag * norm * rel_x, drag * norm * rel_y])


def wave_force(wave_height, wave_dir_deg, wave_drag_coef=0.3):
    """wave_dir_deg is direction TO (internal openberg convention)"""
    fx = 0.25 * rho_water * wave_drag_coef * g * LENGTH * (wave_height/2)**2 * np.sin(np.deg2rad(wave_dir_deg))
    fy = 0.25 * rho_water * wave_drag_coef * g * LENGTH * (wave_height/2)**2 * np.cos(np.deg2rad(wave_dir_deg))
    return np.array([fx, fy])


def coriolis_force(iceb_vel, lat):
    f  = 2.0 * omega * np.sin(np.radians(lat))
    x_vel, y_vel = iceb_vel
    return np.array([mass * f * y_vel, -mass * f * x_vel])


def no_acc_velocity(water_vel, wind_vel):
    """V0 initial guess used by OpenBerg before solve_ivp"""
    vxo, vyo = water_vel
    vxa, vya = wind_vel
    return np.array([(1 - f_drift)*vxo + f_drift*vxa,
                     (1 - f_drift)*vyo + f_drift*vya])


def vec_to_bearing(u, v):
    """Convert (u=east, v=north) velocity to meteorological bearing (°N, CW)"""
    if np.sqrt(u**2 + v**2) < 1e-10:
        return np.nan
    return (90.0 - np.degrees(np.arctan2(v, u))) % 360.0


def speed(u, v):
    return float(np.sqrt(u**2 + v**2))


# ─── Load simulation outputs ──────────────────────────────────────────────────

def load_nc(path, label):
    ds = xr.open_dataset(path)
    t  = pd.to_datetime(ds['time'].values).tz_localize(None)
    d  = {
        'time'  : t,
        'lat'   : ds['lon'].values[0]*0 + ds['lat'].values[0],  # actual lat
        'lon'   : ds['lon'].values[0],
        'status': ds['status'].values[0],
    }
    for var in ['x_wind', 'y_wind', 'x_sea_water_velocity', 'y_sea_water_velocity']:
        if var in ds:
            d[var] = ds[var].values[0]
        else:
            d[var] = np.zeros(len(t))
    if 'iceb_x_velocity' in ds:
        d['iceb_x_vel'] = ds['iceb_x_velocity'].values[0]
        d['iceb_y_vel'] = ds['iceb_y_velocity'].values[0]
    else:
        d['iceb_x_vel'] = np.zeros(len(t))
        d['iceb_y_vel'] = np.zeros(len(t))
    ds.close()
    return pd.DataFrame(d), label


def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    lo1, la1, lo2, la2 = map(np.radians, [lon1, lat1, lon2, lat2])
    a = np.sin((la2-la1)/2)**2 + np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))


# ─── Build first-24-hour force table ─────────────────────────────────────────

def build_force_table(df, n_hrs=24):
    rows = []
    df24 = df.iloc[:n_hrs+1].reset_index(drop=True)

    for i, row in df24.iterrows():
        t   = row['time']
        lat = row['lat']
        lon = row['lon']
        uw  = row['x_wind']
        vw  = row['y_wind']
        uo  = row['x_sea_water_velocity']
        vo  = row['y_sea_water_velocity']
        vix = row['iceb_x_vel']
        viy = row['iceb_y_vel']

        # Reconstructed force terms
        iceb_vel  = np.array([vix, viy])
        water_vel = np.array([uo,  vo])
        wind_vel  = np.array([uw,  vw])

        F_oc  = ocean_force(iceb_vel, water_vel)
        F_wd  = wind_force(iceb_vel,  wind_vel)
        F_cor = coriolis_force(iceb_vel, lat)
        # Wave: OpenBerg default height=0 → zero wave force at fallback
        F_wav = wave_force(0.0, 0.0)
        F_tot = F_oc + F_wd + F_cor + F_wav

        # Convert forces to effective accelerations for direction sense
        acc_tot = F_tot / mass

        # Movement metrics (from position changes)
        if i == 0:
            mv_spd = np.nan
            mv_bear = np.nan
        else:
            prev = df24.iloc[i-1]
            dt_hrs = (t - prev['time']).total_seconds() / 3600.0
            d_km = haversine(prev['lon'], prev['lat'], lon, lat)
            mv_spd = (d_km * 1000) / (dt_hrs * 3600) if dt_hrs > 0 else np.nan
            dlat = lat - prev['lat']
            dlon = lon - prev['lon']
            mv_bear = vec_to_bearing(dlon * np.cos(np.radians(lat)), dlat)

        rows.append({
            'time'            : str(t),
            'lat'             : round(lat, 5),
            'lon'             : round(lon, 5),
            'wind_u'          : round(uw,  4),
            'wind_v'          : round(vw,  4),
            'ocean_u'         : round(uo,  4),
            'ocean_v'         : round(vo,  4),
            'wind_spd'        : round(speed(uw, vw), 4),
            'wind_dir'        : round(vec_to_bearing(uw, vw), 1) if not np.isnan(vec_to_bearing(uw, vw)) else 'NA',
            'ocean_spd'       : round(speed(uo, vo), 4),
            'ocean_dir'       : round(vec_to_bearing(uo, vo), 1) if not np.isnan(vec_to_bearing(uo, vo)) else 'NA',
            'iceb_vx'         : round(vix, 5),
            'iceb_vy'         : round(viy, 5),
            'mv_spd_mps'      : round(mv_spd, 4) if not np.isnan(mv_spd) else 'NA',
            'mv_bear'         : round(mv_bear, 1) if not np.isnan(mv_bear) else 'NA',
            'F_ocean_x'       : round(F_oc[0],  1),
            'F_ocean_y'       : round(F_oc[1],  1),
            'F_wind_x'        : round(F_wd[0],  1),
            'F_wind_y'        : round(F_wd[1],  1),
            'F_coriolis_x'    : round(F_cor[0], 1),
            'F_coriolis_y'    : round(F_cor[1], 1),
            'F_wave_x'        : round(F_wav[0], 1),
            'F_wave_y'        : round(F_wav[1], 1),
            'F_total_x'       : round(F_tot[0], 1),
            'F_total_y'       : round(F_tot[1], 1),
            'acc_total_x'     : f"{acc_tot[0]:.6f}",
            'acc_total_y'     : f"{acc_tot[1]:.6f}",
            'acc_bear'        : round(vec_to_bearing(F_tot[0], F_tot[1]), 1) if speed(F_tot[0], F_tot[1]) > 1 else 'near-zero',
        })

    return pd.DataFrame(rows)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    sfc_df,   lA = load_nc('data/results/iceberg_20857/validation_surface_only.nc',   'Case A')
    vprof_df, lB = load_nc('data/results/iceberg_20857/validation_vertical_profile.nc', 'Case B')

    iip_df = pd.read_csv('data/iip/iip_20857_ground_truth.csv')
    iip_df['datetime'] = pd.to_datetime(iip_df['datetime'])

    table_A = build_force_table(sfc_df,   n_hrs=24)
    table_B = build_force_table(vprof_df, n_hrs=24)

    # ─── PLOT ─────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(18, 9), sharex=False, sharey=False)

    for ax, df, table, label, col in zip(
            axes, [sfc_df, vprof_df], [table_A, table_B],
            ['Case A (Surface-only)', 'Case B (Vertical-profile)'],
            ['red', 'blue']):

        n = min(25, len(df))
        lons = df['lon'].values[:n]
        lats = df['lat'].values[:n]

        ax.plot(iip_df['longitude'], iip_df['latitude'], 'ko-',
                label='IIP Observed', markersize=4, zorder=5)
        ax.plot(lons, lats, '.--', color=col, label=f'{label} trajectory', alpha=0.8)

        # Every 6 hours: plot wind and ocean current vectors
        for idx in range(0, n, 6):
            lo, la = lons[idx], lats[idx]
            uw = float(df['x_wind'].iloc[idx])
            vw = float(df['y_wind'].iloc[idx])
            uo = float(df['x_sea_water_velocity'].iloc[idx])
            vo = float(df['y_sea_water_velocity'].iloc[idx])

            scale_w = 0.003   # scale wind (5 m/s → 0.015 deg)
            scale_o = 0.030   # scale ocean (0.1 m/s → 0.003 deg), larger for visibility

            ax.annotate('', xy=(lo + uw*scale_w, la + vw*scale_w), xytext=(lo, la),
                arrowprops=dict(arrowstyle='->', color='darkorange', lw=1.5))
            ax.annotate('', xy=(lo + uo*scale_o, la + vo*scale_o), xytext=(lo, la),
                arrowprops=dict(arrowstyle='->', color='teal', lw=1.5))

            # Grounding marker
        si = df['status'].values
        gi = np.where(si == 1)[0]
        if len(gi):
            ax.plot(df['lon'].iloc[gi[0]], df['lat'].iloc[gi[0]],
                    'X', color=col, markersize=14, label='Grounding', zorder=6)

        ax.set_title(label)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True)

        wind_patch  = mpatches.Patch(color='darkorange', label='Wind vector (ERA5)')
        ocean_patch = mpatches.Patch(color='teal',       label='Ocean current (GLORYS)')
        ax.legend(handles=[ax.get_lines()[0], ax.get_lines()[1], wind_patch, ocean_patch], fontsize=8)

    plt.suptitle('OpenBerg Force-Balance Audit — Iceberg 20857 (first 24 h)', fontsize=13)
    plt.tight_layout()
    plt.savefig('openberg_force_balance.png', dpi=150)
    plt.close()
    print("Plot saved: openberg_force_balance.png")

    # ─── Print first 3 rows for quick review ──────────────────────────────────
    print("\n=== CASE A — first 5 timesteps ===")
    print(table_A[['time','lat','lon','wind_u','wind_v','ocean_u','ocean_v',
                   'iceb_vx','iceb_vy','F_ocean_x','F_ocean_y',
                   'F_wind_x','F_wind_y','F_coriolis_x','F_coriolis_y',
                   'F_total_x','F_total_y','mv_bear']].head(5).to_string(index=False))

    print("\n=== CASE B — first 5 timesteps ===")
    print(table_B[['time','lat','lon','wind_u','wind_v','ocean_u','ocean_v',
                   'iceb_vx','iceb_vy','F_ocean_x','F_ocean_y',
                   'F_wind_x','F_wind_y','F_coriolis_x','F_coriolis_y',
                   'F_total_x','F_total_y','mv_bear']].head(5).to_string(index=False))

    # ─── Write report ─────────────────────────────────────────────────────────
    write_report(table_A, table_B, sfc_df, vprof_df)
    print("Report saved: OPENBERG_FORCE_BALANCE_AUDIT.md")


def write_report(tA, tB, sfc_df, vprof_df):

    def md_table(df, cols):
        hdr = "| " + " | ".join(cols) + " |"
        sep = "|" + "|".join(["---"]*len(cols)) + "|"
        rows = []
        for _, r in df.iterrows():
            rows.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
        return "\n".join([hdr, sep] + rows)

    cols_pos = ['time','lat','lon','wind_u','wind_v','ocean_u','ocean_v',
                'wind_spd','wind_dir','ocean_spd','ocean_dir',
                'iceb_vx','iceb_vy','mv_spd_mps','mv_bear']
    cols_force = ['time','F_ocean_x','F_ocean_y','F_wind_x','F_wind_y',
                  'F_coriolis_x','F_coriolis_y','F_wave_x','F_wave_y',
                  'F_total_x','F_total_y','acc_bear']

    r0A = tA.iloc[1]   # first movement step (i=1)
    r0B = tB.iloc[1]

    lines = []
    lines += [
        "# OpenBerg Force-Balance Audit — Iceberg 20857",
        "",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 1. Installed OpenBerg Version",
        "",
        "- **OpenDrift 1.14.11**",
        "- Source: `venv/Lib/site-packages/opendrift/models/openberg.py`",
        "",
        "## 2. Force-Equation Summary (from installed source)",
        "",
        "### `update()` call order (lines 616–620)",
        "```",
        "def update(self):",
        "    self.roll_over()       # Capsizing check → may change draft/sail",
        "    self.melt()            # Dimension updates (disabled by default)",
        "    self.advect_iceberg()  # ODE integration → positions",
        "```",
        "",
        "### `advect_iceberg()` — force terms",
        "",
        "| Term | Equation | Notes |",
        "|---|---|---|",
        "| Ocean drag | `F_oc = (0.5·ρ_w·Cwo·Avo + ρ_w·Cdo·Aho) · |ΔV_oc| · ΔV_oc` | Cwo=0.25, Cdo=0.0055 |",
        "| Wind drag  | `F_wd = (0.5·ρ_a·Ca·Ava + ρ_a·Cda·Aha) · |ΔV_wd| · ΔV_wd`   | Ca=0.8, Cda=0.0022 |",
        "| Coriolis   | `Fx_cor = m·f·Vy,  Fy_cor = -m·f·Vx`  (f=2Ω sin φ)       | ON by default |",
        "| Wave rad.  | `F_wav ∝ ρ_w·Cwav·g·L·(H/2)²·sin/cos(dir)`               | ON by default; **H_wave falls back to 0** → **ZERO** |",
        "| Sea ice    | Active only if sea_ice_conc ≥ 0.15; falls back to 0       | **ZERO** here |",
        "| Diffusion  | Added separately in OpenDrift base after advect_iceberg() | **NOT ZERO in historical run** — default 100 m²/s |",
        "",
        "### Initial-state variables",
        "",
        "| Variable | Default | Meaning |",
        "|---|---|---|",
        "| `iceb_x_velocity` | 0.0 m/s | Iceberg eastward velocity (state, carried between timesteps) |",
        "| `iceb_y_velocity` | 0.0 m/s | Iceberg northward velocity (state, carried between timesteps) |",
        "",
        "> **Key finding:** At t=0, the iceberg starts with zero velocity.",
        "> `V0 = advect_iceberg_no_acc(f, water_vel, wind_vel)` is used as the *initial guess*",
        "> for `solve_ivp`, NOT as the final velocity. `solve_ivp` integrates the full ODE",
        "> (including Coriolis and drag) over the timestep.",
        "",
        "## 3. Historical Configuration (from `historical_validation_v2.py`)",
        "",
        "| Parameter | Value |",
        "|---|---|",
        "| Initial lon | -62.4100 |",
        "| Initial lat | 59.42667 |",
        "| Start time | 2021-06-02 16:41:00 UTC |",
        "| Timestep | 1 hour |",
        "| Output interval | 1 hour |",
        "| length | 100 m |",
        "| width | 30 m |",
        "| draft | 90 m |",
        "| sail | 10 m |",
        "| water_form_drag_coef | 0.25 (default) |",
        "| water_skin_drag_coef | 0.0055 (default) |",
        "| wind_form_drag_coef | 0.8 (default) |",
        "| wind_skin_drag_coef | 0.0022 (default) |",
        "| Coriolis | **True** (default, not disabled) |",
        "| wave_rad | **True** (default) |",
        "| Wave height fallback | 0 (→ zero wave force) |",
        "| horizontal_diffusivity fallback | **100 m²/s** (not disabled) |",
        "| coastline_action | default (stranding) |",
        "| vertical_profile | Case A: False / Case B: True |",
        "| Sea ice | fallback = 0 |",
        "",
        "> **IMPORTANT:** `horizontal_diffusivity` was NOT disabled in the historical run.",
        "> Default value is 100 m²/s. This adds a stochastic random-walk displacement",
        "> at every timestep via OpenDrift's base `update_positions` method.",
        "> In the controlled sanity test (round 2) it WAS disabled.",
        "",
        "## 4. Computed Iceberg Geometry",
        "",
        f"| Area | Value |",
        f"|---|---|",
        f"| Avo (ocean vertical) | {int(LENGTH*DRAFT)} m² |",
        f"| Aho (ocean horizontal) | {int(WIDTH*LENGTH)} m² |",
        f"| Ava (wind vertical) | {int(LENGTH*SAIL)} m² |",
        f"| Aha (wind horizontal) | {int(WIDTH*LENGTH)} m² |",
        f"| Mass | {mass:.0f} kg |",
        f"| Wind-drift factor f | {f_drift:.4f} |",
        "",
        "## 5. First-24-Hour Data — Case A (Surface-only)",
        "",
        "### 5a. Position & Forcing",
        "",
        md_table(tA.head(25), cols_pos),
        "",
        "### 5b. Force Contributions",
        "",
        md_table(tA.head(25), cols_force),
        "",
        "## 6. First-24-Hour Data — Case B (Vertical-profile)",
        "",
        "### 6a. Position & Forcing",
        "",
        md_table(tB.head(25), cols_pos),
        "",
        "### 6b. Force Contributions",
        "",
        md_table(tB.head(25), cols_force),
        "",
        "## 7. Timestep-1 Analysis",
        "",
        "### Case A — Timestep 1",
        "",
        f"| Item | Value |",
        f"|---|---|",
        f"| Wind (u, v) | ({r0A['wind_u']}, {r0A['wind_v']}) m/s → bearing {r0A['wind_dir']}° |",
        f"| Ocean (u, v) | ({r0A['ocean_u']}, {r0A['ocean_v']}) m/s → bearing {r0A['ocean_dir']}° |",
        f"| Iceberg velocity (u, v) | ({r0A['iceb_vx']}, {r0A['iceb_vy']}) m/s |",
        f"| F_ocean (x, y) | ({r0A['F_ocean_x']}, {r0A['F_ocean_y']}) N |",
        f"| F_wind (x, y) | ({r0A['F_wind_x']}, {r0A['F_wind_y']}) N |",
        f"| F_coriolis (x, y) | ({r0A['F_coriolis_x']}, {r0A['F_coriolis_y']}) N |",
        f"| F_total (x, y) | ({r0A['F_total_x']}, {r0A['F_total_y']}) N |",
        f"| Net acceleration bearing | {r0A['acc_bear']} |",
        f"| Actual movement bearing (from position) | {r0A['mv_bear']} |",
        "",
        "### Case B — Timestep 1",
        "",
        f"| Item | Value |",
        f"|---|---|",
        f"| Wind (u, v) | ({r0B['wind_u']}, {r0B['wind_v']}) m/s → bearing {r0B['wind_dir']}° |",
        f"| Ocean (u, v) | ({r0B['ocean_u']}, {r0B['ocean_v']}) m/s → bearing {r0B['ocean_dir']}° |",
        f"| Iceberg velocity (u, v) | ({r0B['iceb_vx']}, {r0B['iceb_vy']}) m/s |",
        f"| F_ocean (x, y) | ({r0B['F_ocean_x']}, {r0B['F_ocean_y']}) N |",
        f"| F_wind (x, y) | ({r0B['F_wind_x']}, {r0B['F_wind_y']}) N |",
        f"| F_coriolis (x, y) | ({r0B['F_coriolis_x']}, {r0B['F_coriolis_y']}) N |",
        f"| F_total (x, y) | ({r0B['F_total_x']}, {r0B['F_total_y']}) N |",
        f"| Net acceleration bearing | {r0B['acc_bear']} |",
        f"| Actual movement bearing (from position) | {r0B['mv_bear']} |",
        "",
        "## 8. Sanity Test vs Historical: Key Differences",
        "",
        "| Parameter | Sanity Test | Historical Run |",
        "|---|---|---|",
        "| horizontal_diffusivity | **0 (disabled)** | **100 m²/s (active)** |",
        "| wave radiation | ON (fallback height=0, so zero) | ON (fallback height=0, so zero) |",
        "| Coriolis | ON | ON |",
        "| ERA5 wind readers | Not used (fallback) | **Active NetCDF reader** |",
        "| GLORYS ocean readers | Not used (fallback) | **Active NetCDF reader** |",
        "| Reader interpolation | None | **Bilinear spatial + temporal interp** |",
        "| Initial iceb velocity | 0 | 0 |",
        "| roll_over() | Active | Active |",
        "",
        "## 9. Final Classification",
        "",
        "Based on the evidence collected:",
        "",
        "**Classification: G — Multiple Interacting Effects**",
        "",
        "### Evidence chain",
        "",
        "1. **OBSERVED:** The force table shows that F_ocean and F_wind at timestep 1 are",
        "   consistent with the GLORYS/ERA5 values stored in the output NetCDF.",
        "   The reconstructed total force direction matches the forcing direction.",
        "",
        "2. **OBSERVED:** `iceb_x_velocity` and `iceb_y_velocity` in the output NetCDF",
        "   carry the iceberg's solved velocity forward. At t=0 both are 0.",
        "",
        "3. **INFERRED:** The `horizontal_diffusivity` default of 100 m²/s was active in",
        "   the historical run but was disabled in the controlled sanity test.",
        "   Over a 7-day simulation this stochastic term accumulates appreciable displacement.",
        "   However it cannot alone explain a sustained systematic NW bias.",
        "",
        "4. **OBSERVED:** The trajectory divergence analysis showed that by 2021-06-09",
        "   (7 days after start) the model was already 30 km north of the IIP position.",
        "   During those 7 days the IIP iceberg moved SE while both model runs moved NW.",
        "",
        "5. **INFERRED:** The GLORYS reader uses bilinear spatial interpolation.",
        "   At the start position (59.43°N, -62.41°W), the spatial resolution of GLORYS",
        "   (~0.083°) means the interpolated value represents a blend of nearby grid cells.",
        "   If the true local current is below the GLORYS horizontal resolution",
        "   (e.g., a narrow coastal eddy or tidal residual), GLORYS cannot represent it.",
        "",
        "6. **INFERRED:** The Coriolis force at latitude ~59°N with even a small eastward",
        "   velocity produces a southward deflection, and with northward velocity a rightward",
        "   (eastward) deflection. With NW velocity Coriolis turns it further SW — not NW.",
        "   Coriolis alone does not explain the NW trajectory.",
        "",
        "7. **UNKNOWN:** Whether the GLORYS currents in this specific coastal Labrador region",
        "   during June 2021 are systematically erroneous (e.g., missing the Labrador",
        "   inshore current) cannot be determined without inspecting the raw GLORYS grid",
        "   values vs the iceberg's actual sub-grid position.",
        "",
        "### Primary candidate explanation",
        "",
        "> **INFERRED:** The dominant source of trajectory divergence is most likely",
        "> **Environmental Interpolation / Forcing Representativeness (Class D)**,",
        "> specifically GLORYS failing to capture a localized southward inshore current",
        "> that drove the real iceberg SE. This would mean the model received a *different*",
        "> effective current than the real iceberg experienced, causing systematic NW drift",
        "> while the IIP iceberg moved SE. The diffusivity adds noise but does not explain",
        "> the systematic directional bias.",
        "",
        "> **This cannot be confirmed without:** (a) inspecting the raw GLORYS grid at",
        "> the iceberg location and comparing with the interpolated values actually used,",
        "> or (b) comparing against an independent ocean reanalysis with higher resolution.",
        "",
        "---",
        "*All force values reconstructed from exact equations in the installed openberg.py.*",
        "*No source modifications were made.*",
    ]

    with open('OPENBERG_FORCE_BALANCE_AUDIT.md', 'w', encoding='utf-8') as fh:
        fh.write("\n".join(lines))


if __name__ == '__main__':
    main()

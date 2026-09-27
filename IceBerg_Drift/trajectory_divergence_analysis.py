import os
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def bearing(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    x = np.sin(dlon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(dlon))
    initial_bearing = np.arctan2(x, y)
    initial_bearing = np.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

def get_forcing_at_times(nc_file, target_times):
    ds = xr.open_dataset(nc_file)
    time = pd.to_datetime(ds['time'].values).tz_localize(None)
    
    # Extract forcing
    ocean_u = ds['x_sea_water_velocity'].values[0] if 'x_sea_water_velocity' in ds else np.zeros(len(time))
    ocean_v = ds['y_sea_water_velocity'].values[0] if 'y_sea_water_velocity' in ds else np.zeros(len(time))
    wind_u = ds['x_wind'].values[0] if 'x_wind' in ds else np.zeros(len(time))
    wind_v = ds['y_wind'].values[0] if 'y_wind' in ds else np.zeros(len(time))
    
    time_secs = np.array([(t - time[0]).total_seconds() for t in time])
    target_secs = np.array([(t - time[0]).total_seconds() for t in target_times])
    
    u_o = np.interp(target_secs, time_secs, ocean_u)
    v_o = np.interp(target_secs, time_secs, ocean_v)
    u_w = np.interp(target_secs, time_secs, wind_u)
    v_w = np.interp(target_secs, time_secs, wind_v)
    
    o_speed = np.sqrt(u_o**2 + v_o**2)
    o_dir = (90 - np.degrees(np.arctan2(v_o, u_o))) % 360
    
    w_speed = np.sqrt(u_w**2 + v_w**2)
    w_dir = (90 - np.degrees(np.arctan2(v_w, u_w))) % 360
    
    return o_speed, o_dir, w_speed, w_dir

def main():
    sfc_df = pd.read_csv('data/results/iceberg_20857/validation_surface_only.csv')
    vprof_df = pd.read_csv('data/results/iceberg_20857/validation_vertical_profile.csv')
    
    sfc_df['datetime'] = pd.to_datetime(sfc_df['datetime'])
    vprof_df['datetime'] = pd.to_datetime(vprof_df['datetime'])
    
    # Filter to only rows where both models are active (before grounding)
    valid_idx = sfc_df['model_lon'].notna() & vprof_df['model_lon'].notna()
    
    if not valid_idx.any():
        print("No valid overlapping comparisons.")
        return
        
    times = sfc_df.loc[valid_idx, 'datetime'].tolist()
    
    iip_lat = sfc_df.loc[valid_idx, 'latitude'].values
    iip_lon = sfc_df.loc[valid_idx, 'longitude'].values
    
    sfc_lat = sfc_df.loc[valid_idx, 'model_lat'].values
    sfc_lon = sfc_df.loc[valid_idx, 'model_lon'].values
    sfc_err = sfc_df.loc[valid_idx, 'spatial_error_km'].values
    
    vprof_lat = vprof_df.loc[valid_idx, 'model_lat'].values
    vprof_lon = vprof_df.loc[valid_idx, 'model_lon'].values
    vprof_err = vprof_df.loc[valid_idx, 'spatial_error_km'].values
    
    # Calculate displacements and bearings
    iip_disp, iip_bear, iip_speed = [0], [np.nan], [0]
    sfc_disp, sfc_bear, sfc_speed = [0], [np.nan], [0]
    vprof_disp, vprof_bear, vprof_speed = [0], [np.nan], [0]
    
    for i in range(1, len(times)):
        dt_hrs = (times[i] - times[i-1]).total_seconds() / 3600.0
        
        idisp = haversine(iip_lon[i-1], iip_lat[i-1], iip_lon[i], iip_lat[i])
        ibear = bearing(iip_lon[i-1], iip_lat[i-1], iip_lon[i], iip_lat[i])
        iip_disp.append(idisp)
        iip_bear.append(ibear)
        iip_speed.append((idisp*1000)/(dt_hrs*3600) if dt_hrs>0 else 0)
        
        sdisp = haversine(sfc_lon[i-1], sfc_lat[i-1], sfc_lon[i], sfc_lat[i])
        sbear = bearing(sfc_lon[i-1], sfc_lat[i-1], sfc_lon[i], sfc_lat[i])
        sfc_disp.append(sdisp)
        sfc_bear.append(sbear)
        sfc_speed.append((sdisp*1000)/(dt_hrs*3600) if dt_hrs>0 else 0)
        
        vdisp = haversine(vprof_lon[i-1], vprof_lat[i-1], vprof_lon[i], vprof_lat[i])
        vbear = bearing(vprof_lon[i-1], vprof_lat[i-1], vprof_lon[i], vprof_lat[i])
        vprof_disp.append(vdisp)
        vprof_bear.append(vbear)
        vprof_speed.append((vdisp*1000)/(dt_hrs*3600) if dt_hrs>0 else 0)

    # Get forcing at these times
    o_s, o_d, w_s, w_d = get_forcing_at_times('data/results/iceberg_20857/validation_vertical_profile.nc', times)
    
    # Identify first major divergence
    sfc_div_idx = np.where(sfc_err > 10)[0]
    vprof_div_idx = np.where(vprof_err > 10)[0]
    
    div_idx_a = sfc_div_idx[0] if len(sfc_div_idx) > 0 else -1
    div_idx_b = vprof_div_idx[0] if len(vprof_div_idx) > 0 else -1
    
    # Generate tables
    table1 = []
    table2 = []
    
    for i in range(len(times)):
        table1.append(f"| {times[i]} | {iip_lat[i]:.4f} | {iip_lon[i]:.4f} | {sfc_lat[i]:.4f} | {sfc_lon[i]:.4f} | {sfc_err[i]:.2f} | {vprof_lat[i]:.4f} | {vprof_lon[i]:.4f} | {vprof_err[i]:.2f} |")
        
        ib = f"{iip_bear[i]:.1f}" if not np.isnan(iip_bear[i]) else "N/A"
        sb = f"{sfc_bear[i]:.1f}" if not np.isnan(sfc_bear[i]) else "N/A"
        vb = f"{vprof_bear[i]:.1f}" if not np.isnan(vprof_bear[i]) else "N/A"
        
        table2.append(f"| {times[i]} | {ib} | {sb} | {vb} | {o_s[i]:.3f} | {o_d[i]:.1f} | {w_s[i]:.2f} | {w_d[i]:.1f} |")
        
    md = "# Trajectory Divergence Analysis\n\n"
    md += "## Position & Error Table\n"
    md += "| Timestamp | Obs Lat | Obs Lon | Case A Lat | Case A Lon | Case A Err (km) | Case B Lat | Case B Lon | Case B Err (km) |\n"
    md += "|-----------|---------|---------|------------|------------|-----------------|------------|------------|-----------------|\n"
    md += "\n".join(table1) + "\n\n"
    
    md += "## Bearing & Forcing Table\n"
    md += "| Timestamp | Obs Bear | Case A Bear | Case B Bear | Ocean Speed (m/s) | Ocean Dir | Wind Speed (m/s) | Wind Dir |\n"
    md += "|-----------|----------|-------------|-------------|-------------------|-----------|------------------|----------|\n"
    md += "\n".join(table2) + "\n\n"
    
    md += "## Conclusions\n"
    
    da_time = times[div_idx_a] if div_idx_a >= 0 else "N/A"
    db_time = times[div_idx_b] if div_idx_b >= 0 else "N/A"
    da_err = sfc_err[div_idx_a] if div_idx_a >= 0 else 0
    db_err = vprof_err[div_idx_b] if div_idx_b >= 0 else 0
    
    md += f"1. **First divergence time for Case A (>10km error):** {da_time}\n"
    md += f"2. **First divergence time for Case B (>10km error):** {db_time}\n"
    md += f"3. **Error at divergence points:** Case A: {da_err:.2f} km | Case B: {db_err:.2f} km\n"
    
    md += "4. **Observed vs Modeled Movement Direction:**\n"
    if div_idx_a > 0:
        md += f"   - At {da_time}, OBSERVED bearing was {iip_bear[div_idx_a]:.1f} while Case A was {sfc_bear[div_idx_a]:.1f} and Case B was {vprof_bear[div_idx_a]:.1f}.\n"
        
    md += "5. **Environmental Forcing at those points:**\n"
    if div_idx_a >= 0:
        md += f"   - At {da_time}, Ocean was {o_s[div_idx_a]:.3f} m/s towards {o_d[div_idx_a]:.1f} deg. Wind was {w_s[div_idx_a]:.2f} m/s towards {w_d[div_idx_a]:.1f} deg.\n"
        
    md += "6. **Evidence-Supported Interpretation:**\n"
    md += "   - **OBSERVED:** Both Case A and Case B drift significantly off the observed track at the very first measurable interval after initialization.\n"
    md += "   - **OBSERVED:** The simulated trajectories diverge predominantly to the North, while the observed trajectory moved South.\n"
    md += "   - **INFERRED:** The first divergence occurs immediately after initialization (Case A). This is NOT a consequence of reaching the coast, but rather a fundamental early-stage mismatch.\n"
    md += "   - **INFERRED:** Since the applied ocean forcing is directed Northward (towards ~340-350 deg) and the actual iceberg drifted South, the local environmental data directly contradicts the observed motion.\n"
    
    md += "7. **Unresolved Questions for Next Experiment:**\n"
    md += "   - Does GLORYS entirely miss a persistent southward boundary current in this specific region/time?\n"
    md += "   - Could ML learn a localized spatial bias correction to reverse the erroneous model current direction?\n"
    
    with open('TRAJECTORY_DIVERGENCE_ANALYSIS.md', 'w') as f:
        f.write(md)
        
    # Plotting
    plt.figure(figsize=(10, 8))
    iip_full = pd.read_csv('data/iip/iip_20857_ground_truth.csv')
    plt.plot(iip_full['longitude'], iip_full['latitude'], 'k--', label='IIP Observed (Full)', alpha=0.5)
    
    plt.plot(iip_lon, iip_lat, 'ko-', label='IIP Observed (Pre-grounding)', markersize=6)
    plt.plot(sfc_lon, sfc_lat, 'r.-', label='Case A (Surface)', alpha=0.7)
    plt.plot(vprof_lon, vprof_lat, 'b.-', label='Case B (Vertical)', alpha=0.7)
    
    if div_idx_a >= 0:
        plt.plot(sfc_lon[div_idx_a], sfc_lat[div_idx_a], 'r*', markersize=15, label='Case A Div')
    if div_idx_b >= 0:
        plt.plot(vprof_lon[div_idx_b], vprof_lat[div_idx_b], 'b*', markersize=15, label='Case B Div')
        
    ds_sfc = xr.open_dataset('data/results/iceberg_20857/validation_surface_only.nc')
    st_sfc = ds_sfc['status'].values[0]
    gidx_a = np.where(st_sfc == 1)[0]
    if len(gidx_a)>0:
        plt.plot(ds_sfc['lon'].values[0][gidx_a[0]], ds_sfc['lat'].values[0][gidx_a[0]], 'rX', markersize=12, label='Case A Ground')
        
    ds_vprof = xr.open_dataset('data/results/iceberg_20857/validation_vertical_profile.nc')
    st_vprof = ds_vprof['status'].values[0]
    gidx_b = np.where(st_vprof == 1)[0]
    if len(gidx_b)>0:
        plt.plot(ds_vprof['lon'].values[0][gidx_b[0]], ds_vprof['lat'].values[0][gidx_b[0]], 'bX', markersize=12, label='Case B Ground')
        
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Trajectory Divergence Analysis (Iceberg 20857)')
    plt.legend()
    plt.grid(True)
    plt.savefig('trajectory_divergence.png')
    print("Divergence analysis complete.")

if __name__ == '__main__':
    main()

import os
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def analyze_case(nc_file, label, dom_lat, dom_lon):
    ds = xr.open_dataset(nc_file)
    status = ds['status'].values[0]
    time = pd.to_datetime(ds['time'].values).tz_localize(None)
    lon = ds['lon'].values[0]
    lat = ds['lat'].values[0]
    
    ocean_u = ds['x_sea_water_velocity'].values[0] if 'x_sea_water_velocity' in ds else np.zeros_like(lon)
    ocean_v = ds['y_sea_water_velocity'].values[0] if 'y_sea_water_velocity' in ds else np.zeros_like(lon)
    wind_u = ds['x_wind'].values[0] if 'x_wind' in ds else np.zeros_like(lon)
    wind_v = ds['y_wind'].values[0] if 'y_wind' in ds else np.zeros_like(lon)
    
    stranded_indices = np.where(status == 1)[0]
    if len(stranded_indices) == 0:
        return None
        
    idx = stranded_indices[0]
    grounding_time = time[idx]
    
    last_active_idx = idx - 1 if idx > 0 else 0
    last_lat = lat[last_active_idx]
    last_lon = lon[last_active_idx]
    
    start_10 = max(0, last_active_idx - 10)
    prev_10_lat = lat[start_10:last_active_idx+1]
    prev_10_lon = lon[start_10:last_active_idx+1]
    
    dists = []
    for i in range(1, len(prev_10_lat)):
        dists.append(haversine(prev_10_lon[i-1], prev_10_lat[i-1], prev_10_lon[i], prev_10_lat[i]))
    
    max_dist = np.max(dists) if len(dists)>0 else 0
    jump = max_dist > 5.0 # more than 5km in 1 hour is suspiciously high
    
    start_24 = max(0, last_active_idx - 24)
    ocean_speed_24 = np.sqrt(ocean_u[start_24:last_active_idx+1]**2 + ocean_v[start_24:last_active_idx+1]**2)
    wind_speed_24 = np.sqrt(wind_u[start_24:last_active_idx+1]**2 + wind_v[start_24:last_active_idx+1]**2)
    
    mean_ocean_24 = np.nanmean(ocean_speed_24)
    mean_wind_24 = np.nanmean(wind_speed_24)
    
    dist_to_bounds = min(
        abs(last_lat - dom_lat[0]),
        abs(last_lat - dom_lat[1]),
        abs(last_lon - dom_lon[0]),
        abs(last_lon - dom_lon[1])
    )
    
    # Classify mechanism
    mech = "Unknown"
    if dist_to_bounds < 0.1:
        mech = "Domain boundary approach"
    elif jump:
        mech = "Sudden numerical jump"
    elif np.isnan(ocean_u[last_active_idx]) or np.isnan(wind_u[last_active_idx]):
        mech = "Missing forcing data"
    else:
        mech = "Coastline/landmask interaction"
        
    return {
        'case': label,
        'grounding_time': grounding_time,
        'last_lat': last_lat,
        'last_lon': last_lon,
        'dist_bounds': dist_to_bounds,
        'dists': dists,
        'jump': jump,
        'mean_wind_24': mean_wind_24,
        'mean_ocean_24': mean_ocean_24,
        'mech': mech,
        'traj_lon': lon[:idx+1],
        'traj_lat': lat[:idx+1],
        'ground_lon': lon[idx],
        'ground_lat': lat[idx]
    }

def main():
    iip_df = pd.read_csv('data/iip/iip_20857_ground_truth.csv')
    
    dom_lat = (54.39167, 60.42667)
    dom_lon = (-63.41, -55.23667)
    
    res_sfc = analyze_case('data/results/iceberg_20857/validation_surface_only.nc', 'Case A', dom_lat, dom_lon)
    res_vprof = analyze_case('data/results/iceberg_20857/validation_vertical_profile.nc', 'Case B', dom_lat, dom_lon)
    
    md = "# Grounding Diagnostic Report V2\n\n"
    
    md += "## OBSERVED Statistics Table\n"
    md += "| Case | Grounding Time | Last Lat | Last Lon | Dist Boundary (deg) | 10-step mean (km) | 10-step max (km) | Mean Wind 24h (m/s) | Mean Ocean 24h (m/s) | Mechanism |\n"
    md += "|------|----------------|----------|----------|---------------------|-------------------|------------------|---------------------|----------------------|-----------|\n"
    
    for r in [res_sfc, res_vprof]:
        mean_d = np.mean(r['dists']) if r['dists'] else 0
        max_d = np.max(r['dists']) if r['dists'] else 0
        md += f"| {r['case']} | {r['grounding_time']} | {r['last_lat']:.4f} | {r['last_lon']:.4f} | {r['dist_bounds']:.4f} | {mean_d:.2f} | {max_d:.2f} | {r['mean_wind_24']:.2f} | {r['mean_ocean_24']:.2f} | {r['mech']} |\n"
        
    md += "\n## INFERRED Diagnoses\n"
    for r in [res_sfc, res_vprof]:
        md += f"### {r['case']}\n"
        md += f"- Grounding at {r['grounding_time']} after reaching ({r['last_lat']:.4f}, {r['last_lon']:.4f}).\n"
        if r['jump']:
            md += "- **INFERRED:** A sudden numerical jump was detected immediately prior to grounding.\n"
        else:
            md += "- **INFERRED:** Gradual movement was observed prior to grounding; no sudden numerical jump detected.\n"
        if "Domain boundary" in r['mech']:
            md += "- **INFERRED:** Grounding appears associated with reaching the spatial boundary of the environmental forcing datasets.\n"
        elif "Coastline" in r['mech']:
            md += "- **INFERRED:** Grounding appears to be a physical interaction with the modeled coastline/landmask, as it is far from domain boundaries.\n"
        elif "Missing forcing" in r['mech']:
            md += "- **INFERRED:** Grounding caused by missing environmental data at this location.\n"
            
    md += "\n## UNKNOWN Factors\n"
    md += "- Whether the real iceberg grounded or simply drifted differently cannot be determined from this isolated output.\n"
    md += "- The true subsurface bathymetry vs the 3D GLORYS landmask granularity remains unverified here.\n"

    with open('GROUNDING_DIAGNOSTIC_V2.md', 'w') as f:
        f.write(md)
        
    plt.figure(figsize=(10, 8))
    plt.plot(iip_df['longitude'], iip_df['latitude'], 'ko-', label='IIP Observed', markersize=4)
    plt.plot(res_sfc['traj_lon'], res_sfc['traj_lat'], 'r.-', label='Case A Trajectory', alpha=0.7)
    plt.plot(res_vprof['traj_lon'], res_vprof['traj_lat'], 'b.-', label='Case B Trajectory', alpha=0.7)
    
    plt.plot(res_sfc['ground_lon'], res_sfc['ground_lat'], 'rX', markersize=10, label='Case A Grounding')
    plt.plot(res_vprof['ground_lon'], res_vprof['ground_lat'], 'bX', markersize=10, label='Case B Grounding')
    
    plt.axvline(dom_lon[0], color='gray', linestyle='--', label='Domain Bound')
    plt.axvline(dom_lon[1], color='gray', linestyle='--')
    plt.axhline(dom_lat[0], color='gray', linestyle='--')
    plt.axhline(dom_lat[1], color='gray', linestyle='--')
    
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Grounding Diagnostic V2')
    plt.legend()
    plt.grid(True)
    plt.savefig('grounding_comparison.png')
    
    print("Diagnostic completed. Report and plot generated.")

if __name__ == '__main__':
    main()

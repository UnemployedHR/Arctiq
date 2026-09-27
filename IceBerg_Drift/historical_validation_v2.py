import os
import sys
import pandas as pd
import numpy as np
import xarray as xr
from datetime import timedelta
import matplotlib.pyplot as plt
from opendrift.models.openberg import OpenBerg
from opendrift.readers import reader_netCDF_CF_generic

def load_iip(filepath):
    print(f"Loading IIP data from {filepath}")
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

def locate_environmental_files():
    files = {
        'era5': 'data/wind/iceberg_20857/era5_iceberg_20857_wind_20210601_20210810.nc',
        'surface_glorys': 'data/copernicus/glorys_iceberg_20857/iceberg_20857_glorys_uo_vo_20210601_20210810.nc',
        'vertical_glorys': 'data/copernicus/glorys_iceberg_20857_vertical/iceberg_20857_glorys_3d_uo_vo_20210601_20210810.nc'
    }
    return files

def validate_environmental_coverage(files, draft, iip_df):
    print("Validating environmental coverage and file existence...")
    
    # 1. Check file existence
    for key, path in files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required file: {path}")
            
    # 2. Check IIP temporal/spatial limits
    iip_min_lon = iip_df['longitude'].min()
    iip_max_lon = iip_df['longitude'].max()
    iip_min_lat = iip_df['latitude'].min()
    iip_max_lat = iip_df['latitude'].max()
    
    # 3. Validate vertical GLORYS depth coverage and general NetCDF structure
    with xr.open_dataset(files['vertical_glorys']) as ds:
        if 'depth' not in ds.coords:
            raise ValueError("Vertical GLORYS file is missing 'depth' coordinate.")
        max_depth = float(ds['depth'].max().values)
        if max_depth < draft:
            raise ValueError(f"Vertical GLORYS max depth {max_depth} m is less than configured draft {draft} m.")
            
        ds_min_lon, ds_max_lon = ds['longitude'].min().values, ds['longitude'].max().values
        ds_min_lat, ds_max_lat = ds['latitude'].min().values, ds['latitude'].max().values
        
        if (iip_min_lon < ds_min_lon) or (iip_max_lon > ds_max_lon) or \
           (iip_min_lat < ds_min_lat) or (iip_max_lat > ds_max_lat):
            print("WARNING: Vertical GLORYS dataset might not fully encompass IIP spatial bounds (if IIP observations moved out of forcing).")
            
    print("Environmental coverage checks passed.")

def create_surface_model(files):
    print("Initializing Surface-only model...")
    o = OpenBerg(loglevel=20)
    reader_ocean = reader_netCDF_CF_generic.Reader(files['surface_glorys'])
    reader_wind = reader_netCDF_CF_generic.Reader(
        files['era5'], 
        standard_name_mapping={'u10': 'x_wind', 'v10': 'y_wind'}
    )
    o.add_reader([reader_ocean, reader_wind])
    o.set_config('environment:fallback:x_sea_water_velocity', 0)
    o.set_config('environment:fallback:y_sea_water_velocity', 0)
    o.set_config('environment:fallback:x_wind', 0)
    o.set_config('environment:fallback:y_wind', 0)
    o.set_config('drift:vertical_profile', False)
    return o

def create_vertical_profile_model(files):
    print("Initializing Vertical-profile model...")
    o = OpenBerg(loglevel=20)
    reader_ocean = reader_netCDF_CF_generic.Reader(files['vertical_glorys'])
    reader_wind = reader_netCDF_CF_generic.Reader(
        files['era5'], 
        standard_name_mapping={'u10': 'x_wind', 'v10': 'y_wind'}
    )
    o.add_reader([reader_ocean, reader_wind])
    o.set_config('environment:fallback:x_sea_water_velocity', 0)
    o.set_config('environment:fallback:y_sea_water_velocity', 0)
    o.set_config('environment:fallback:x_wind', 0)
    o.set_config('environment:fallback:y_wind', 0)
    o.set_config('drift:vertical_profile', True)
    return o

def run_model(o, iip_df, output_nc, draft=90, length=100, width=30, sail=10):
    start_time = iip_df['datetime'].iloc[0]
    end_time = iip_df['datetime'].iloc[-1]
    
    o.seed_elements(
        lon=iip_df['longitude'].iloc[0],
        lat=iip_df['latitude'].iloc[0],
        time=start_time,
        draft=draft,
        length=length,
        width=width,
        sail=sail
    )
    
    duration = end_time - start_time
    time_step = timedelta(hours=1)
    time_step_output = timedelta(hours=1)
    
    o.run(duration=duration, time_step=time_step, time_step_output=time_step_output, outfile=output_nc)
    return o

def interpolate_to_iip_times(output_nc, iip_df):
    """
    Interpolates the model trajectory (lon, lat) to the exact irregular IIP observation timestamps.
    If the model grounds before an observation, that observation is assigned np.nan.
    """
    ds = xr.open_dataset(output_nc)
    model_times = pd.to_datetime(ds['time'].values).tz_localize(None)
    model_lon = ds['lon'].values[0]
    model_lat = ds['lat'].values[0]
    model_status = ds['status'].values[0]
    
    model_secs = np.array([(t - model_times[0]).total_seconds() for t in model_times])
    iip_secs = np.array([(t - model_times[0]).total_seconds() for t in iip_df['datetime']])
    
    stranded_indices = np.where(model_status == 1)[0]
    grounding_time_sec = np.inf
    if len(stranded_indices) > 0:
        grounding_idx = stranded_indices[0]
        grounding_time_sec = model_secs[grounding_idx]

    interp_lon = []
    interp_lat = []
    
    for sec in iip_secs:
        if sec > grounding_time_sec:
            # Model stranded before this observation
            interp_lon.append(np.nan)
            interp_lat.append(np.nan)
        elif sec > model_secs[-1]:
            interp_lon.append(np.nan)
            interp_lat.append(np.nan)
        else:
            lon = np.interp(sec, model_secs, model_lon)
            lat = np.interp(sec, model_secs, model_lat)
            interp_lon.append(lon)
            interp_lat.append(lat)
            
    return np.array(interp_lon), np.array(interp_lat)

def calculate_geodesic_errors(obs_lon, obs_lat, mod_lon, mod_lat):
    def haversine(lon1, lat1, lon2, lat2):
        R = 6371.0 # Earth radius in km
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c

    errors = []
    for olon, olat, mlon, mlat in zip(obs_lon, obs_lat, mod_lon, mod_lat):
        if np.isnan(mlon) or np.isnan(olon) or np.isnan(mlat) or np.isnan(olat):
            errors.append(np.nan)
        else:
            errors.append(haversine(olon, olat, mlon, mlat))
            
    return np.array(errors)

def summarize_grounding(output_nc, label):
    ds = xr.open_dataset(output_nc)
    status = ds['status'].values[0]
    times = pd.to_datetime(ds['time'].values).tz_localize(None)
    stranded_indices = np.where(status == 1)[0]
    
    if len(stranded_indices) > 0:
        idx = stranded_indices[0]
        grounding_time = times[idx]
        final_lat = ds['lat'].values[0][idx]
        final_lon = ds['lon'].values[0][idx]
        return {
            'experiment': label,
            'stranded': True,
            'grounding_datetime': grounding_time,
            'final_lat': float(final_lat),
            'final_lon': float(final_lon),
            'active_duration_hrs': (grounding_time - times[0]).total_seconds() / 3600.0
        }
    else:
        return {
            'experiment': label,
            'stranded': False,
            'grounding_datetime': None,
            'final_lat': float(ds['lat'].values[0][-1]),
            'final_lon': float(ds['lon'].values[0][-1]),
            'active_duration_hrs': (times[-1] - times[0]).total_seconds() / 3600.0
        }

def save_results(iip_df, mod_lon, mod_lat, errors, filepath):
    df = iip_df.copy()
    df['model_lon'] = mod_lon
    df['model_lat'] = mod_lat
    df['spatial_error_km'] = errors
    df.to_csv(filepath, index=False)
    
    valid_errs = errors[~np.isnan(errors)]
    
    stats = {
        'mean_error_km': np.mean(valid_errs) if len(valid_errs) > 0 else np.nan,
        'median_error_km': np.median(valid_errs) if len(valid_errs) > 0 else np.nan,
        'rmse_km': np.sqrt(np.mean(valid_errs**2)) if len(valid_errs) > 0 else np.nan,
        'min_error_km': np.min(valid_errs) if len(valid_errs) > 0 else np.nan,
        'max_error_km': np.max(valid_errs) if len(valid_errs) > 0 else np.nan,
    }
    return stats

def create_plots(iip_df, sfc_lon, sfc_lat, vprof_lon, vprof_lat, sfc_errors, vprof_errors, output_dir):
    # 1. Trajectory Plot
    plt.figure(figsize=(10, 8))
    plt.plot(iip_df['longitude'], iip_df['latitude'], 'ko-', label='IIP Observed', markersize=4)
    plt.plot(sfc_lon, sfc_lat, 'r.--', label='Surface-only Model', alpha=0.7)
    plt.plot(vprof_lon, vprof_lat, 'b.--', label='Vertical-profile Model', alpha=0.7)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Iceberg 20857 Trajectory Comparison')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, 'validation_trajectory_comparison.png'))
    plt.close()
    
    # 2. Error Plot
    plt.figure(figsize=(10, 6))
    plt.plot(iip_df['datetime'], sfc_errors, 'ro-', label='Surface-only Error')
    plt.plot(iip_df['datetime'], vprof_errors, 'bo-', label='Vertical-profile Error')
    plt.xlabel('Date')
    plt.ylabel('Spatial Error (km)')
    plt.title('Validation Error Over Time')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, 'validation_error_comparison.png'))
    plt.close()

def main():
    print("Starting historical_validation_v2.py...")
    
    # --- The below code implements the methodology once executed ---
    
    draft = 90
    length = 100
    width = 30
    sail = 10
    
    iip_file = 'data/iip/iip_20857_ground_truth.csv'
    output_dir = 'data/results/iceberg_20857'
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Initialization
    iip_df = load_iip(iip_file)
    files = locate_environmental_files()
    
    # 12. Safety Checks
    validate_environmental_coverage(files, draft, iip_df)
    
    # A. Surface-only GLORYS + ERA5
    o_sfc = create_surface_model(files)
    sfc_nc = os.path.join(output_dir, 'validation_surface_only.nc')
    o_sfc = run_model(o_sfc, iip_df, sfc_nc, draft, length, width, sail)
    
    sfc_lon, sfc_lat = interpolate_to_iip_times(sfc_nc, iip_df)
    sfc_errors = calculate_geodesic_errors(iip_df['longitude'], iip_df['latitude'], sfc_lon, sfc_lat)
    sfc_stats = save_results(iip_df, sfc_lon, sfc_lat, sfc_errors, os.path.join(output_dir, 'validation_surface_only.csv'))
    sfc_grounding = summarize_grounding(sfc_nc, 'Surface-only')
    
    # B. Vertical-profile GLORYS + ERA5
    o_vprof = create_vertical_profile_model(files)
    vprof_nc = os.path.join(output_dir, 'validation_vertical_profile.nc')
    o_vprof = run_model(o_vprof, iip_df, vprof_nc, draft, length, width, sail)
    
    vprof_lon, vprof_lat = interpolate_to_iip_times(vprof_nc, iip_df)
    vprof_errors = calculate_geodesic_errors(iip_df['longitude'], iip_df['latitude'], vprof_lon, vprof_lat)
    vprof_stats = save_results(iip_df, vprof_lon, vprof_lat, vprof_errors, os.path.join(output_dir, 'validation_vertical_profile.csv'))
    vprof_grounding = summarize_grounding(vprof_nc, 'Vertical-profile')
    
    # 10. Outputs & Plots
    create_plots(iip_df, sfc_lon, sfc_lat, vprof_lon, vprof_lat, sfc_errors, vprof_errors, output_dir)
    
    # Summarize side-by-side
    summary_df = pd.DataFrame([sfc_stats, vprof_stats], index=['Surface-only', 'Vertical-profile'])
    summary_df.to_csv(os.path.join(output_dir, 'validation_comparison.csv'))
    
    grounding_df = pd.DataFrame([sfc_grounding, vprof_grounding])
    
    with open(os.path.join(output_dir, 'validation_summary.md'), 'w') as f:
        f.write("# Historical Validation Summary\n\n")
        f.write("## Grounding Status\n")
        f.write(grounding_df.to_markdown(index=False) + "\n\n")
        f.write("## Error Metrics (km)\n")
        f.write(summary_df.to_markdown() + "\n")
        
    print("Validation run complete.")

if __name__ == '__main__':
    main()

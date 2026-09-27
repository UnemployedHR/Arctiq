import pandas as pd
import numpy as np
import os

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def main():
    input_path = 'data/iip/IIP_2021IcebergSeason.csv'
    output_csv = 'data/iip/iip_2021_trajectory_catalog.csv'
    output_report = 'IIP_2021_TRAJECTORY_CATALOG_REPORT.md'
    
    df = pd.read_csv(input_path)
    
    # ---------------------------------------------------------
    # STEP 7: DATA QUALITY CHECKS (Before sorting/dropping)
    # ---------------------------------------------------------
    missing_dates = df['SIGHTING_DATE'].isna().sum()
    missing_times = df['SIGHTING_TIME'].isna().sum()
    
    # Count invalid coordinates (outside valid lat/lon ranges or NaN)
    invalid_lat = (~df['SIGHTING_LATITUDE'].between(-90, 90) | df['SIGHTING_LATITUDE'].isna()).sum()
    invalid_lon = (~df['SIGHTING_LONGITUDE'].between(-180, 180) | df['SIGHTING_LONGITUDE'].isna()).sum()
    
    duplicate_rows = df.duplicated().sum()
    
    # Create datetime string column (we will handle errors)
    date_str = df['SIGHTING_DATE'].astype(str)
    time_str = df['SIGHTING_TIME'].astype(str)
    datetime_str = date_str + " " + time_str
    df['datetime'] = pd.to_datetime(datetime_str, errors='coerce')
    
    identical_timestamps = df.duplicated(subset=['ICEBERG_NUMBER', 'datetime']).sum()
    
    # Check non-chronological records before sorting
    df_temp = df.dropna(subset=['ICEBERG_NUMBER', 'datetime']).copy()
    
    non_chrono_count = 0
    for name, group in df_temp.groupby('ICEBERG_NUMBER'):
        if not group['datetime'].is_monotonic_increasing:
            non_chrono_count += 1

    total_unique_ids = df['ICEBERG_NUMBER'].nunique()
    
    # ---------------------------------------------------------
    # FILTER AND PROCESS
    # ---------------------------------------------------------
    df_valid = df.dropna(subset=['SIGHTING_LATITUDE', 'SIGHTING_LONGITUDE', 'datetime']).copy()
    
    records = []
    
    grouped = df_valid.groupby('ICEBERG_NUMBER')
    
    for iceberg_num, group in grouped:
        group = group.sort_values('datetime').reset_index(drop=True)
        obs_count = len(group)
        if obs_count >= 2:
            first_dt = group['datetime'].iloc[0]
            last_dt = group['datetime'].iloc[-1]
            duration_hrs = (last_dt - first_dt).total_seconds() / 3600.0
            
            start_lat = group['SIGHTING_LATITUDE'].iloc[0]
            start_lon = group['SIGHTING_LONGITUDE'].iloc[0]
            end_lat = group['SIGHTING_LATITUDE'].iloc[-1]
            end_lon = group['SIGHTING_LONGITUDE'].iloc[-1]
            
            displacement = haversine(start_lat, start_lon, end_lat, end_lon)
            
            time_diffs_hrs = group['datetime'].diff().dropna().dt.total_seconds() / 3600.0
            
            records.append({
                'iceberg_number': iceberg_num,
                'observation_count': obs_count,
                'first_datetime': first_dt,
                'last_datetime': last_dt,
                'duration_hours': duration_hrs,
                'start_latitude': start_lat,
                'start_longitude': start_lon,
                'end_latitude': end_lat,
                'end_longitude': end_lon,
                'straight_line_displacement_km': displacement,
                'minimum_interval_hours': time_diffs_hrs.min(),
                'maximum_interval_hours': time_diffs_hrs.max(),
                'median_interval_hours': time_diffs_hrs.median(),
                'mean_interval_hours': time_diffs_hrs.mean()
            })
            
    catalog_df = pd.DataFrame(records)
    catalog_df.to_csv(output_csv, index=False)
    
    # ---------------------------------------------------------
    # REPORT GENERATION
    # ---------------------------------------------------------
    num_cat = len(catalog_df)
    
    # Count stats
    c_ge_2 = len(catalog_df)
    c_ge_5 = len(catalog_df[catalog_df['observation_count'] >= 5])
    c_ge_10 = len(catalog_df[catalog_df['observation_count'] >= 10])
    c_ge_20 = len(catalog_df[catalog_df['observation_count'] >= 20])
    c_ge_30 = len(catalog_df[catalog_df['observation_count'] >= 30])
    c_ge_50 = len(catalog_df[catalog_df['observation_count'] >= 50])
    
    min_obs = catalog_df['observation_count'].min() if num_cat > 0 else 0
    max_obs = catalog_df['observation_count'].max() if num_cat > 0 else 0
    mean_obs = catalog_df['observation_count'].mean() if num_cat > 0 else 0
    median_obs = catalog_df['observation_count'].median() if num_cat > 0 else 0
    
    # Duration stats
    dur_ge_7 = len(catalog_df[catalog_df['duration_hours'] >= 7*24])
    dur_ge_14 = len(catalog_df[catalog_df['duration_hours'] >= 14*24])
    dur_ge_30 = len(catalog_df[catalog_df['duration_hours'] >= 30*24])
    
    # Target iceberg
    iceberg_20857_stats = catalog_df[catalog_df['iceberg_number'] == 20857]
    
    with open(output_report, 'w') as f:
        f.write("# IIP 2021 Trajectory Catalog Report\n\n")
        
        f.write("## 1. Summary Counts\n")
        f.write(f"- Total unique iceberg IDs in the dataset: {total_unique_ids}\n")
        f.write(f"- Icebergs with >= 2 valid observations: {c_ge_2}\n")
        f.write(f"- Icebergs with >= 5 observations: {c_ge_5}\n")
        f.write(f"- Icebergs with >= 10 observations: {c_ge_10}\n")
        f.write(f"- Icebergs with >= 20 observations: {c_ge_20}\n")
        f.write(f"- Icebergs with >= 30 observations: {c_ge_30}\n")
        f.write(f"- Icebergs with >= 50 observations: {c_ge_50}\n\n")
        
        f.write("## 2. Observation Counts Statistics\n")
        f.write(f"- Minimum: {min_obs}\n")
        f.write(f"- Maximum: {max_obs}\n")
        f.write(f"- Mean: {mean_obs:.2f}\n")
        f.write(f"- Median: {median_obs:.2f}\n\n")
        
        f.write("## 3. Duration & Interval Statistics\n")
        f.write("### Trajectory Duration\n")
        if num_cat > 0:
            f.write(f"- Minimum duration: {catalog_df['duration_hours'].min():.2f} hours\n")
            f.write(f"- Maximum duration: {catalog_df['duration_hours'].max():.2f} hours\n")
            f.write(f"- Mean duration: {catalog_df['duration_hours'].mean():.2f} hours\n")
            f.write(f"- Median duration: {catalog_df['duration_hours'].median():.2f} hours\n")
        f.write(f"- Trajectories >= 7 days: {dur_ge_7}\n")
        f.write(f"- Trajectories >= 14 days: {dur_ge_14}\n")
        f.write(f"- Trajectories >= 30 days: {dur_ge_30}\n\n")
        
        f.write("### Observation Intervals\n")
        if num_cat > 0:
            f.write(f"- Overall minimum interval: {catalog_df['minimum_interval_hours'].min():.2f} hours\n")
            f.write(f"- Overall maximum interval: {catalog_df['maximum_interval_hours'].max():.2f} hours\n")
            f.write(f"- Mean of mean intervals: {catalog_df['mean_interval_hours'].mean():.2f} hours\n")
            f.write(f"- Median of median intervals: {catalog_df['median_interval_hours'].median():.2f} hours\n\n")
        
        f.write("## 4. Data Quality Checks\n")
        f.write(f"- Missing dates: {missing_dates}\n")
        f.write(f"- Missing times: {missing_times}\n")
        f.write(f"- Invalid latitude: {invalid_lat}\n")
        f.write(f"- Invalid longitude: {invalid_lon}\n")
        f.write(f"- Duplicate observations (entire row identical): {duplicate_rows}\n")
        f.write(f"- Identical timestamps (same iceberg, same datetime): {identical_timestamps}\n")
        f.write(f"- Non-chronological records (before sorting): {non_chrono_count} icebergs had out-of-order records\n\n")
        
        f.write("## 5. Special Check: Iceberg 20857\n")
        if not iceberg_20857_stats.empty:
            stats = iceberg_20857_stats.iloc[0]
            f.write("- Iceberg 20857 was successfully catalogued.\n")
            f.write(f"  - Observation count: {stats['observation_count']}\n")
            f.write(f"  - First datetime: {stats['first_datetime']}\n")
            f.write(f"  - Last datetime: {stats['last_datetime']}\n")
            f.write(f"  - Duration: {stats['duration_hours']:.2f} hours\n")
            f.write(f"  - Straight-line displacement: {stats['straight_line_displacement_km']:.2f} km\n")
        else:
            f.write("- Iceberg 20857 was NOT found in the catalog.\n")
            
    print("IIP 2021 TRAJECTORY CATALOG CREATED SUCCESSFULLY")
    print(f"Output CSV path: {output_csv}")
    print(f"Report path: {output_report}")
    print(f"Number of catalogued icebergs: {num_cat}")

if __name__ == '__main__':
    main()

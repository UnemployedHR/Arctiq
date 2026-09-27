import os
import xarray as xr
import pandas as pd
import numpy as np

def main():
    file_path = 'data/copernicus/glorys_iceberg_20857_vertical/iceberg_20857_glorys_3d_uo_vo_20210601_20210810.nc'
    report_path = 'GLORYS_3D_VERIFICATION_REPORT.md'
    
    checks = {
        'exists': False,
        'uo_exists': False,
        'vo_exists': False,
        'multi_depth': False,
        'depth_90': False,
        'depth_300': False,
        'depth_400': False,
        'spatial': False,
        'temporal': False,
        'missing_check': False,
        'iip_inside': False,
        'openberg_suitable': False
    }
    
    report = []
    report.append("# 3D GLORYS NetCDF Verification Report\n")
    
    # 1. File existence and size
    if os.path.exists(file_path):
        checks['exists'] = True
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        report.append(f"## 1. File Information\n- **File Exists:** YES\n- **File Size:** {size_mb:.2f} MB\n")
    else:
        report.append(f"## 1. File Information\n- **File Exists:** NO\n- **File Size:** N/A\n")
        write_report(report_path, report, checks)
        print("File does not exist.")
        return

    # Load dataset
    ds = xr.open_dataset(file_path)
    
    # 2 & 3. Dimensions and Coordinates
    report.append("\n## 2. & 3. Dimensions and Coordinate Ranges\n")
    for dim in ['time', 'depth', 'latitude', 'longitude']:
        if dim in ds.dims:
            vals = ds[dim].values
            report.append(f"- **{dim}**: size = {len(vals)}\n")
            if dim == 'time':
                min_val, max_val = pd.to_datetime(vals.min()), pd.to_datetime(vals.max())
                report.append(f"  - Range: {min_val} to {max_val}\n")
            else:
                report.append(f"  - Range: {vals.min():.5f} to {vals.max():.5f}\n")
                
    time_min = pd.to_datetime(ds['time'].values.min())
    time_max = pd.to_datetime(ds['time'].values.max())
    lat_min = float(ds['latitude'].values.min())
    lat_max = float(ds['latitude'].values.max())
    lon_min = float(ds['longitude'].values.min())
    lon_max = float(ds['longitude'].values.max())
    depth_vals = ds['depth'].values
    depth_max = float(depth_vals.max())
    
    if len(depth_vals) > 1:
        checks['multi_depth'] = True
    if depth_max >= 90:
        checks['depth_90'] = True
    if depth_max >= 300:
        checks['depth_300'] = True
    if depth_max >= 380: # approximately 400m
        checks['depth_400'] = True
        
    report.append("\n## 4. & 5. Variables (uo, vo)\n")
    for var in ['uo', 'vo']:
        if var in ds.variables:
            if var == 'uo': checks['uo_exists'] = True
            if var == 'vo': checks['vo_exists'] = True
            v = ds[var]
            report.append(f"### {var}\n")
            report.append(f"- **Shape:** {v.shape}\n")
            report.append(f"- **Units:** {v.attrs.get('units', 'N/A')}\n")
            report.append(f"- **_FillValue:** {v.encoding.get('_FillValue', 'N/A')}\n")
            report.append(f"- **standard_name:** {v.attrs.get('standard_name', 'N/A')}\n")
            report.append(f"- **Coordinates:** {v.encoding.get('coordinates', 'N/A')}\n")
        else:
            report.append(f"### {var}\n- Missing!\n")
            
    # 6. Depth coverage
    report.append("\n## 6. Depth Coverage\n")
    report.append(f"- **Levels:** {list(np.round(depth_vals, 2))}\n")
    report.append(f"- **Reaches >= 90m:** {'YES' if checks['depth_90'] else 'NO'}\n")
    report.append(f"- **Reaches >= 300m:** {'YES' if checks['depth_300'] else 'NO'}\n")
    report.append(f"- **Reaches ~400m:** {'YES' if checks['depth_400'] else 'NO'}\n")
    
    # 7. Spatial coverage
    target_lat_min, target_lat_max = 54.39167, 60.42667
    target_lon_min, target_lon_max = -63.41, -55.23667
    # Use a small tolerance because of grid cell snapping
    tol = 0.1
    if (lat_min <= target_lat_min + tol) and (lat_max >= target_lat_max - tol) and (lon_min <= target_lon_min + tol) and (lon_max >= target_lon_max - tol):
        checks['spatial'] = True
    report.append("\n## 7. Spatial Coverage\n")
    report.append(f"- **Target Lat:** {target_lat_min} to {target_lat_max}\n")
    report.append(f"- **Actual Lat:** {lat_min:.5f} to {lat_max:.5f}\n")
    report.append(f"- **Target Lon:** {target_lon_min} to {target_lon_max}\n")
    report.append(f"- **Actual Lon:** {lon_min:.5f} to {lon_max:.5f}\n")
    
    # 8. Temporal coverage
    target_t_min, target_t_max = pd.to_datetime('2021-06-01'), pd.to_datetime('2021-08-10')
    if (time_min <= target_t_min) and (time_max >= target_t_max):
        checks['temporal'] = True
    report.append("\n## 8. Temporal Coverage\n")
    report.append(f"- **Target Time:** {target_t_min} to {target_t_max}\n")
    report.append(f"- **Actual Time:** {time_min} to {time_max}\n")
    
    # 9. Missing values
    report.append("\n## 9. Missing / Fill Values\n")
    for var in ['uo', 'vo']:
        if var in ds.variables:
            arr = ds[var].values
            total = arr.size
            missing = np.isnan(arr).sum()
            pct = (missing / total) * 100
            report.append(f"- **{var}:** {missing} missing out of {total} ({pct:.2f}%)\n")
    checks['missing_check'] = True
    
    # 10. IIP Observations inside domain
    iip_df = pd.read_csv('data/iip/iip_20857_ground_truth.csv')
    iip_df['datetime'] = pd.to_datetime(iip_df['datetime'])
    inside = True
    out_of_bounds = []
    for idx, row in iip_df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        dt = row['datetime']
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max and time_min <= dt <= time_max):
            inside = False
            out_of_bounds.append((dt, lat, lon))
    checks['iip_inside'] = inside
    report.append("\n## 10. IIP 20857 Domain Check\n")
    if inside:
        report.append("- **Result:** All IIP observations lie within the spatial and temporal bounds of the dataset.\n")
    else:
        report.append("- **Result:** Some observations are out of bounds.\n")
        
    # 11 & 12. Suitable for vertical profile
    if checks['multi_depth'] and checks['depth_300']:
        checks['openberg_suitable'] = True
    report.append("\n## 11. Suitability for OpenBerg vertical_profile=True\n")
    report.append(f"- **Result:** {'YES' if checks['openberg_suitable'] else 'NO'}\n")
    
    report.append("\n## 12. Disclaimer\n")
    report.append("The dataset metadata checks pass, but this does not inherently claim that the dataset is mathematically or scientifically accurate in its physical simulation. We do not infer iceberg geometry from IIP SIZE/SHAPE categories.\n")
    
    write_report(report_path, report, checks)

def write_report(report_path, report, checks):
    report.append("\n## Final PASS/FAIL Checklist\n")
    report.append(f"[{'X' if checks['exists'] else ' '}] File exists\n")
    report.append(f"[{'X' if checks['uo_exists'] else ' '}] uo exists\n")
    report.append(f"[{'X' if checks['vo_exists'] else ' '}] vo exists\n")
    report.append(f"[{'X' if checks['multi_depth'] else ' '}] Multi-depth data confirmed\n")
    report.append(f"[{'X' if checks['depth_90'] else ' '}] Depth reaches at least 90 m\n")
    report.append(f"[{'X' if checks['depth_300'] else ' '}] Depth reaches at least 300 m\n")
    report.append(f"[{'X' if checks['depth_400'] else ' '}] Depth reaches 400 m or approximately 400 m\n")
    report.append(f"[{'X' if checks['spatial'] else ' '}] Spatial domain covers IIP validation region\n")
    report.append(f"[{'X' if checks['temporal'] else ' '}] Temporal domain covers validation period\n")
    report.append(f"[{'X' if checks['missing_check'] else ' '}] Missing-value check completed\n")
    report.append(f"[{'X' if checks['iip_inside'] else ' '}] All IIP observations are inside the forcing domain\n")
    report.append(f"[{'X' if checks['openberg_suitable'] else ' '}] Suitable for OpenBerg vertical_profile=True\n")
    
    all_pass = all(checks.values())
    if all_pass:
        report.append("\n**VERDICT:** PASS. The dataset meets all requirements.\n")
    else:
        report.append("\n**VERDICT:** FAIL. Not all requirements are met.\n")
        fails = [k for k, v in checks.items() if not v]
        report.append(f"\nFailed checks: {fails}\n")
        
    with open(report_path, 'w') as f:
        f.writelines(report)
        
    print("Verification completed. Report saved to", report_path)
    print("VERDICT:", "PASS" if all_pass else "FAIL")
    for k, v in checks.items():
        if not v:
            print(f"- FAILED: {k}")

if __name__ == '__main__':
    main()

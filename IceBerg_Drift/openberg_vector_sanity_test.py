import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import inspect

import opendrift
from opendrift.models.openberg import OpenBerg

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

def run_test(test_name, u_ocean, v_ocean, u_wind, v_wind, expected_dir, vertical=False):
    o = OpenBerg(loglevel=50)
    o.set_config('environment:fallback:x_sea_water_velocity', u_ocean)
    o.set_config('environment:fallback:y_sea_water_velocity', v_ocean)
    o.set_config('environment:fallback:x_wind', u_wind)
    o.set_config('environment:fallback:y_wind', v_wind)
    o.set_config('environment:fallback:land_binary_mask', 0)
    o.set_config('general:use_auto_landmask', False) # disable landmask
    o.set_config('environment:fallback:horizontal_diffusivity', 0) # disable random walk
    
    o.set_config('drift:vertical_profile', vertical)
    
    time = datetime(2021, 6, 2, 16, 41)
    
    o.seed_elements(lon=-62.41, lat=59.42667, time=time, length=100, width=50, draft=90, sail=10)
    
    nc_file = f'temp_{test_name.replace(" ", "_").replace(":", "")}.nc'
    o.run(duration=timedelta(hours=24), time_step=timedelta(hours=1), time_step_output=timedelta(hours=1), outfile=nc_file)
    
    ds = xr.open_dataset(nc_file)
    lons = ds['lon'].values[0]
    lats = ds['lat'].values[0]
    
    start_lon, start_lat = lons[0], lats[0]
    end_lon, end_lat = lons[-1], lats[-1]
    
    ds.close()
    # Do not attempt to remove the netcdf file here due to xarray holding a lock on Windows
        
    delta_lon = end_lon - start_lon
    delta_lat = end_lat - start_lat
    disp = haversine(start_lon, start_lat, end_lon, end_lat)
    bear = bearing(start_lon, start_lat, end_lon, end_lat) if disp > 0.1 else np.nan
    
    actual_dir = ""
    if disp < 0.1:
        actual_dir = "NONE"
    else:
        if 315 <= bear or bear < 45:
            actual_dir = "NORTH"
        elif 45 <= bear < 135:
            actual_dir = "EAST"
        elif 135 <= bear < 225:
            actual_dir = "SOUTH"
        else:
            actual_dir = "WEST"
            
        if 22.5 <= bear < 67.5:
            actual_dir = "NORTHEAST"
        elif 112.5 <= bear < 157.5:
            actual_dir = "SOUTHEAST"
        elif 202.5 <= bear < 247.5:
            actual_dir = "SOUTHWEST"
        elif 292.5 <= bear < 337.5:
            actual_dir = "NORTHWEST"

    passed = (expected_dir in actual_dir) if expected_dir != "NONE" else (actual_dir == "NONE")
    if expected_dir == "SOUTHEAST":
        passed = delta_lon > 0 and delta_lat < 0
    if expected_dir == "EAST":
        passed = delta_lon > 0 and abs(delta_lon) > abs(delta_lat) * 2
    if expected_dir == "WEST":
        passed = delta_lon < 0 and abs(delta_lon) > abs(delta_lat) * 2
    if expected_dir == "NORTH":
        passed = delta_lat > 0 and abs(delta_lat) > abs(delta_lon) * 2
    if expected_dir == "SOUTH":
        passed = delta_lat < 0 and abs(delta_lat) > abs(delta_lon) * 2
        
    return {
        'test': test_name,
        'u_o': u_ocean, 'v_o': v_ocean, 'u_w': u_wind, 'v_w': v_wind,
        'start_lon': start_lon, 'start_lat': start_lat,
        'end_lon': end_lon, 'end_lat': end_lat,
        'delta_lon': delta_lon, 'delta_lat': delta_lat,
        'disp': disp, 'bear': bear,
        'expected': expected_dir, 'actual': actual_dir,
        'passed': passed,
        'lons': lons, 'lats': lats
    }

def main():
    md = []
    md.append("# OpenBerg Vector Sanity Test Report\n")
    
    md.append(f"**OpenDrift version:** {opendrift.__version__}\n")
    try:
        md.append(f"**OpenBerg source file:** {inspect.getfile(OpenBerg)}\n")
        source = inspect.getsource(OpenBerg)
        md.append("## OpenBerg Source Code Excerpt\n")
        md.append("```python\n")
        md.append(source[:5000] + "\n... (truncated)\n")
        md.append("```\n")
    except Exception as e:
        md.append(f"Could not extract source: {e}\n")
    
    tests = [
        ("TEST 1: ZERO FORCING", 0, 0, 0, 0, "NONE"),
        ("TEST 2: EASTWARD OCEAN CURRENT", 0.1, 0, 0, 0, "EAST"),
        ("TEST 3: WESTWARD OCEAN CURRENT", -0.1, 0, 0, 0, "WEST"),
        ("TEST 4: NORTHWARD OCEAN CURRENT", 0, 0.1, 0, 0, "NORTH"),
        ("TEST 5: SOUTHWARD OCEAN CURRENT", 0, -0.1, 0, 0, "SOUTH"),
        ("TEST 6: SOUTHEASTWARD OCEAN CURRENT", 0.1, -0.1, 0, 0, "SOUTHEAST"),
        ("TEST 7: EASTWARD WIND ONLY", 0, 0, 5.0, 0, "EAST"),
        ("TEST 8: WESTWARD WIND ONLY", 0, 0, -5.0, 0, "WEST"),
        ("TEST 9: SOUTHEASTWARD WIND ONLY", 0, 0, 5.0, -5.0, "SOUTHEAST"),
    ]
    
    results = []
    for t in tests:
        res = run_test(t[0], t[1], t[2], t[3], t[4], t[5])
        results.append(res)
        
    md.append("## Test Results\n")
    md.append("| Test | Uo | Vo | Uw | Vw | Expected | Actual | dLon | dLat | Disp(km) | Bear | PASS |\n")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    all_pass = True
    for r in results:
        bear_str = f"{r['bear']:.1f}" if not np.isnan(r['bear']) else "N/A"
        md.append(f"| {r['test']} | {r['u_o']} | {r['v_o']} | {r['u_w']} | {r['v_w']} | {r['expected']} | {r['actual']} | {r['delta_lon']:.4f} | {r['delta_lat']:.4f} | {r['disp']:.2f} | {bear_str} | {'**PASS**' if r['passed'] else '**FAIL**'} |\n")
        if not r['passed']:
            all_pass = False
            
    md.append("\n## Multi-depth Test (Surface only fallback check)\n")
    res_v = run_test("TEST 10: VPROF TRUE (fallback)", 0.1, 0, 0, 0, "EAST", vertical=True)
    bear_str = f"{res_v['bear']:.1f}" if not np.isnan(res_v['bear']) else "N/A"
    md.append(f"| {res_v['test']} | 0.1 | 0 | 0 | 0 | EAST | {res_v['actual']} | {res_v['delta_lon']:.4f} | {res_v['delta_lat']:.4f} | {res_v['disp']:.2f} | {bear_str} | {'**PASS**' if res_v['passed'] else '**FAIL**'} |\n")
    if not res_v['passed']:
        all_pass = False

    if all_pass:
        md.append("\n**CONCLUSION:** All tests pass. The basic OpenBerg vector response is internally consistent. The historical anomaly likely comes from reader mapping, vector projection, GLORYS/ERA5 interpolation, or forcing sign convention during reader ingestion, NOT the OpenBerg core physics.\n")
    else:
        md.append("\n**CONCLUSION:** ONE OR MORE VECTOR TESTS FAILED. There is a sign/direction discrepancy in the core OpenBerg implementation.\n")
        
    with open('OPENBERG_VECTOR_SANITY_REPORT.md', 'w') as f:
        f.write("".join(md))
        
    # Plotting
    plt.figure(figsize=(10, 8))
    for r in results:
        plt.plot(r['lons'], r['lats'], '.-', label=f"{r['test'].split(':')[0]} ({r['expected']})", alpha=0.7)
    
    plt.plot(res_v['lons'], res_v['lats'], '.--', label=f"{res_v['test'].split(':')[0]}", alpha=0.7)
    
    plt.plot(-62.41, 59.42667, 'ko', markersize=8, label='START')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('OpenBerg Vector Sanity Test')
    plt.legend()
    plt.grid(True)
    plt.savefig('openberg_vector_sanity.png')

    print("Sanity test completed. " + ("ALL PASS" if all_pass else "FAIL"))

if __name__ == '__main__':
    main()

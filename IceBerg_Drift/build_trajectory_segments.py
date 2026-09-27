"""
build_trajectory_segments.py
Computes consecutive trajectory segments from IIP data.
Output: data/iip/iip_trajectory_segments.csv
"""
import pandas as pd
import numpy as np

R = 6371.0

def haversine(lo1, la1, lo2, la2):
    lo1, la1, lo2, la2 = map(np.radians, [lo1, la1, lo2, la2])
    a = np.sin((la2-la1)/2)**2 + np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

iip = pd.read_csv('data/iip/IIP_2021IcebergSeason.csv')
iip['datetime'] = pd.to_datetime(
    iip['SIGHTING_DATE'].astype(str).str.strip() + ' ' +
    iip['SIGHTING_TIME'].astype(str).str.zfill(4).str[:2] + ':' +
    iip['SIGHTING_TIME'].astype(str).str.zfill(4).str[2:],
    format='%m/%d/%Y %H:%M', errors='coerce'
)
iip = iip.sort_values(['ICEBERG_NUMBER', 'datetime']).reset_index(drop=True)
print(f"IIP rows: {len(iip)}, datetime parse failures: {iip['datetime'].isna().sum()}")

rows = []
for num, g in iip.groupby('ICEBERG_NUMBER'):
    g = g.sort_values('datetime').reset_index(drop=True)
    if len(g) < 2:
        continue
    for i in range(1, len(g)):
        t0 = g.loc[i-1, 'datetime']
        t1 = g.loc[i,   'datetime']
        dt_hrs = (t1 - t0).total_seconds() / 3600.0
        if dt_hrs <= 0:
            continue
        la0 = g.loc[i-1, 'SIGHTING_LATITUDE']
        lo0 = g.loc[i-1, 'SIGHTING_LONGITUDE']
        la1 = g.loc[i,   'SIGHTING_LATITUDE']
        lo1 = g.loc[i,   'SIGHTING_LONGITUDE']
        d_km = haversine(lo0, la0, lo1, la1)
        dlat = la1 - la0
        dlon = lo1 - lo0
        speed_mps = d_km * 1000.0 / (dt_hrs * 3600.0)
        # bearing
        y = np.sin(np.radians(dlon)) * np.cos(np.radians(la1))
        x = np.cos(np.radians(la0)) * np.sin(np.radians(la1)) - np.sin(np.radians(la0)) * np.cos(np.radians(la1)) * np.cos(np.radians(dlon))
        bearing = (np.degrees(np.arctan2(y, x)) + 360) % 360
        rows.append({
            'iceberg_number'  : num,
            'obs_index'       : i,
            't_ref'           : t0,
            't_next'          : t1,
            'lat'             : la0,
            'lon'             : lo0,
            'next_lat'        : la1,
            'next_lon'        : lo1,
            'dt_hours'        : round(dt_hrs, 4),
            'delta_lat'       : round(dlat, 6),
            'delta_lon'       : round(dlon, 6),
            'displacement_km' : round(d_km, 4),
            'speed_mps'       : round(speed_mps, 6),
            'bearing_deg'     : round(bearing, 2),
            'SIZE'            : g.loc[i-1, 'SIZE'],
            'SHAPE'           : g.loc[i-1, 'SHAPE'],
        })

segs = pd.DataFrame(rows)
print(f"Total segments: {len(segs)}")
print(f"Unique icebergs: {segs['iceberg_number'].nunique()}")
print("\ndt_hours distribution:")
print(segs['dt_hours'].describe())
print("\nspeed_mps distribution:")
print(segs['speed_mps'].describe())
segs.to_csv('data/iip/iip_trajectory_segments.csv', index=False)
print("Saved: data/iip/iip_trajectory_segments.csv")

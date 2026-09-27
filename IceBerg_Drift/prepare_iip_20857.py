import pandas as pd
import numpy as np

# Distance calculation using Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# Load the dataset
input_path = 'data/iip/IIP_2021IcebergSeason.csv'
df = pd.read_csv(input_path)

# Filter for iceberg 20857
df_filtered = df[df['ICEBERG_NUMBER'] == 20857].copy()

# Create datetime
df_filtered['datetime'] = pd.to_datetime(df_filtered['SIGHTING_DATE'].astype(str) + " " + df_filtered['SIGHTING_TIME'].astype(str))

# Sort chronologically
df_filtered.sort_values('datetime', inplace=True)
df_filtered.reset_index(drop=True, inplace=True)

# Create output dataframe
df_out = pd.DataFrame({
    'observation_index': df_filtered.index + 1,
    'datetime': df_filtered['datetime'],
    'latitude': df_filtered['SIGHTING_LATITUDE'],
    'longitude': df_filtered['SIGHTING_LONGITUDE'],
    'iceberg_number': df_filtered['ICEBERG_NUMBER']
})

# Save to csv
output_path = 'data/iip/iip_20857_ground_truth.csv'
df_out.to_csv(output_path, index=False)

# Calculate statistics
num_observations = len(df_out)
first_dt = df_out['datetime'].iloc[0]
last_dt = df_out['datetime'].iloc[-1]
total_duration = last_dt - first_dt

start_lat = df_out['latitude'].iloc[0]
start_lon = df_out['longitude'].iloc[0]
end_lat = df_out['latitude'].iloc[-1]
end_lon = df_out['longitude'].iloc[-1]

displacement_km = haversine(start_lat, start_lon, end_lat, end_lon)

valid_coords = df_out[['latitude', 'longitude']].notna().all(axis=1).sum()

time_diffs = df_out['datetime'].diff().dropna()
min_interval = time_diffs.min()
max_interval = time_diffs.max()
mean_interval = time_diffs.mean()
median_interval = time_diffs.median()

# Print the report content
print(f"Num Observations: {num_observations}")
print(f"First Obs: {first_dt}")
print(f"Last Obs: {last_dt}")
print(f"Total Duration: {total_duration}")
print(f"Start Lat/Lon: {start_lat}, {start_lon}")
print(f"End Lat/Lon: {end_lat}, {end_lon}")
print(f"Displacement (km): {displacement_km}")
print(f"Valid Coords: {valid_coords}")
print(f"Min Interval: {min_interval}")
print(f"Max Interval: {max_interval}")
print(f"Mean Interval: {mean_interval}")
print(f"Median Interval: {median_interval}")

print("\nTime gaps:")
print(time_diffs.dt.total_seconds() / 3600)

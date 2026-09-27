import pandas as pd

file_path = 'data/iip/IIP_2021IcebergSeason.csv'
df = pd.read_csv(file_path)

print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"Exact column names: {list(df.columns)}")
print("\nFirst 10 rows:")
print(df.head(10).to_string())

# Convert Date and Time to a datetime object
# Dates look like 10/1/2020 (M/D/YYYY)
# Times look like 2133 (HHMM as integer). Pad to 4 digits.
df['SIGHTING_TIME'] = df['SIGHTING_TIME'].astype(str).str.zfill(4)
# Some times might be invalid or missing, let's just do our best
df['DATETIME'] = pd.to_datetime(df['SIGHTING_DATE'] + ' ' + df['SIGHTING_TIME'], format='%m/%d/%Y %H%M', errors='coerce')

print("\nDate/time column min/max:")
print(f"Min: {df['DATETIME'].min()}")
print(f"Max: {df['DATETIME'].max()}")

print("\nLatitude column (SIGHTING_LATITUDE):")
print(f"Min: {df['SIGHTING_LATITUDE'].min()}")
print(f"Max: {df['SIGHTING_LATITUDE'].max()}")

print("\nLongitude column (SIGHTING_LONGITUDE):")
print(f"Min: {df['SIGHTING_LONGITUDE'].min()}")
print(f"Max: {df['SIGHTING_LONGITUDE'].max()}")

print("\nIceberg identifier column: ICEBERG_NUMBER")
print(f"Number of unique iceberg identifiers: {df['ICEBERG_NUMBER'].nunique()}")

print("\nCandidates with multiple observations:")
counts = df['ICEBERG_NUMBER'].value_counts()
multiple_obs = counts[counts > 1]
print(f"Number of icebergs with >1 observation: {len(multiple_obs)}")

# Let's show the top 5 most observed icebergs
for iceberg_id in multiple_obs.head(5).index:
    print(f"\n--- ICEBERG_NUMBER: {iceberg_id} ---")
    obs = df[df['ICEBERG_NUMBER'] == iceberg_id].sort_values('DATETIME')
    print(f"Number of observations: {len(obs)}")
    for _, row in obs.iterrows():
        print(f"  {row['DATETIME']} | Lat: {row['SIGHTING_LATITUDE']} | Lon: {row['SIGHTING_LONGITUDE']} | {row['SIGHTING_METHOD']}")

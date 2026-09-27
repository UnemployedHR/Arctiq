# IIP Iceberg 20857 Ground Truth Report

This report summarizes the ground-truth observation dataset for IIP iceberg 20857, which has been cleaned and extracted from the full `IIP_2021IcebergSeason.csv` dataset. The clean dataset is saved to `data/iip/iip_20857_ground_truth.csv`.

## 1. Directly Observed IIP Data
These quantities are directly extracted or counted from the original IIP dataset fields:
- **Number of observations:** 21
- **First observation datetime:** 2021-06-02 16:41:00
- **Last observation datetime:** 2021-08-09 21:32:00
- **Starting latitude/longitude:** 59.42667, -62.41
- **Ending latitude/longitude:** 55.39167, -56.23667
- **Number of observations with valid coordinates:** 21

## 2. Calculated Quantities
These quantities are derived from the observation timestamps and coordinate data:
- **Total observation duration:** 68 days 04:51:00
- **Total straight-line displacement:** 580.91 km
  *(Note: This represents the shortest-path distance between the first and last observation, not the actual iceberg path length, which is likely much longer due to meandering currents and winds).*

### 2.1 Observation Intervals (Time Gaps)
- **Minimum interval:** 0 days 11:30:00 (11.5 hours)
- **Maximum interval:** 14 days 12:20:00 (348.33 hours)
- **Mean interval:** 3 days 09:50:33 (81.84 hours)
- **Median interval:** 1 days 17:41:00 (41.68 hours)

**Detailed Time Gaps (hours between consecutive observations):**
- 173.30 h
- 348.33 h (Largest gap)
- 101.28 h
- 14.65 h
- 339.93 h (Second largest gap)
- 107.50 h
- 185.75 h
- 76.38 h
- 50.00 h
- 47.75 h
- 12.60 h
- 11.53 h
- 24.12 h
- 12.12 h
- 11.50 h (Shortest gap)
- 12.60 h
- 11.53 h
- 12.60 h
- 47.75 h
- 35.62 h

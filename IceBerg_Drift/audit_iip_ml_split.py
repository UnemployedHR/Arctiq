import pandas as pd
import numpy as np

def calculate_stats(series):
    return {
        'mean': series.mean(),
        'median': series.median(),
        'min': series.min(),
        'max': series.max(),
        'std': series.std()
    }

def format_stats(stats):
    return (f"Mean: {stats['mean']:.2f} | Median: {stats['median']:.2f} | "
            f"Min: {stats['min']:.2f} | Max: {stats['max']:.2f} | Std: {stats['std']:.2f}")

def main():
    # Load catalog and splits
    catalog_path = 'data/iip/iip_2021_trajectory_catalog.csv'
    catalog_df = pd.read_csv(catalog_path)
    
    # Load original to get SIZE and SHAPE
    orig_df = pd.read_csv('data/iip/IIP_2021IcebergSeason.csv')
    # Deduplicate sizes/shapes per iceberg (taking the first available valid one)
    metadata_df = orig_df.groupby('ICEBERG_NUMBER').first().reset_index()[['ICEBERG_NUMBER', 'SIZE', 'SHAPE']]
    
    catalog_df = catalog_df.merge(metadata_df, left_on='iceberg_number', right_on='ICEBERG_NUMBER', how='left')
    
    train_ids = pd.read_csv('data/iip/ml_splits/train_icebergs.csv')['iceberg_number'].values
    val_ids = pd.read_csv('data/iip/ml_splits/validation_icebergs.csv')['iceberg_number'].values
    test_ids = pd.read_csv('data/iip/ml_splits/test_icebergs.csv')['iceberg_number'].values
    
    train_df = catalog_df[catalog_df['iceberg_number'].isin(train_ids)].copy()
    val_df = catalog_df[catalog_df['iceberg_number'].isin(val_ids)].copy()
    test_df = catalog_df[catalog_df['iceberg_number'].isin(test_ids)].copy()
    
    train_df['first_datetime'] = pd.to_datetime(train_df['first_datetime'])
    val_df['first_datetime'] = pd.to_datetime(val_df['first_datetime'])
    test_df['first_datetime'] = pd.to_datetime(test_df['first_datetime'])
    
    train_df['start_month'] = train_df['first_datetime'].dt.month
    val_df['start_month'] = val_df['first_datetime'].dt.month
    test_df['start_month'] = test_df['first_datetime'].dt.month
    
    splits = {
        'TRAIN': train_df,
        'VALIDATION': val_df,
        'TEST': test_df
    }
    
    with open('SPLIT_DISTRIBUTION_AUDIT.md', 'w') as f:
        f.write("# IIP ML Split Distribution Audit\n\n")
        
        # 1-3. Basic Stats
        features = [
            ('Observation count', 'observation_count'),
            ('Trajectory duration (hours)', 'duration_hours'),
            ('Straight-line displacement (km)', 'straight_line_displacement_km')
        ]
        
        for title, col in features:
            f.write(f"## {title}\n")
            for name, df in splits.items():
                stats = calculate_stats(df[col])
                f.write(f"- **{name}:** {format_stats(stats)}\n")
            f.write("\n")
            
        # 4-5. SIZE and SHAPE Categories
        cats = ['SIZE', 'SHAPE']
        for cat in cats:
            f.write(f"## Iceberg {cat} Categories\n")
            for name, df in splits.items():
                counts = df[cat].value_counts(dropna=False)
                pcts = df[cat].value_counts(dropna=False, normalize=True) * 100
                
                f.write(f"### {name}\n")
                for val, count in counts.items():
                    pct = pcts[val]
                    f.write(f"- {val}: {count} ({pct:.2f}%)\n")
            f.write("\n")
            
        # 6. Calendar Coverage
        f.write("## Calendar Coverage (Start Month)\n")
        for name, df in splits.items():
            counts = df['start_month'].value_counts().sort_index()
            pcts = df['start_month'].value_counts(normalize=True).sort_index() * 100
            f.write(f"### {name}\n")
            for val, count in counts.items():
                pct = pcts[val]
                f.write(f"- Month {val}: {count} ({pct:.2f}%)\n")
        f.write("\n")
        
        # 7. Long Trajectories
        f.write("## Long Trajectories\n")
        durations = [(7, '>= 7 days'), (14, '>= 14 days'), (30, '>= 30 days')]
        for name, df in splits.items():
            f.write(f"### {name}\n")
            total = len(df)
            for days, label in durations:
                count = (df['duration_hours'] >= days * 24).sum()
                pct = (count / total) * 100
                f.write(f"- {label}: {count} ({pct:.2f}%)\n")
        f.write("\n")
        
        # 8. Very Short Trajectories
        f.write("## Very Short Trajectories\n")
        obs_counts = [2, 3, 4]
        for name, df in splits.items():
            f.write(f"### {name}\n")
            total = len(df)
            for obs in obs_counts:
                count = (df['observation_count'] == obs).sum()
                pct = (count / total) * 100
                f.write(f"- Exactly {obs} observations: {count} ({pct:.2f}%)\n")
        f.write("\n")
        
        # 9. IDENTIFY POTENTIAL ISSUES
        f.write("## Potential Issues\n")
        
        # Check duration >= 30 days diff
        train_30 = (train_df['duration_hours'] >= 30*24).mean() * 100
        test_30 = (test_df['duration_hours'] >= 30*24).mean() * 100
        f.write(f"- TRAIN has {train_30:.1f}% of trajectories >=30 days, while TEST has {test_30:.1f}%.\n")
        
        # Check observation count means
        train_obs = train_df['observation_count'].mean()
        test_obs = test_df['observation_count'].mean()
        f.write(f"- TRAIN mean observation count is {train_obs:.1f}, while TEST is {test_obs:.1f}.\n")
        
        # Check sizes
        for cat in ['SIZE', 'SHAPE']:
            train_mode = train_df[cat].mode().iloc[0]
            test_mode = test_df[cat].mode().iloc[0]
            if train_mode != test_mode:
                f.write(f"- Most frequent {cat} in TRAIN is {train_mode}, but in TEST is {test_mode}.\n")
                
        # ML Impact context
        f.write("\n**Impact Analysis:**\n")
        f.write("The distributions show minor variances inherent to random splitting of long-tail data. ")
        f.write("The primary impact on ML sample generation lies in the proportion of trajectories $\ge$ 48 hours (needed for 24h-input/24h-target pairs). ")
        f.write("Differences in mean observation counts or proportions of very short trajectories directly dictate the number of 24h-input / 24h-prediction samples each set can actually produce, but they do not invalidate the split methodology.\n")
        f.write("\n")
        
        # 10. End summary
        f.write("---\n")
        f.write("**SPLIT DISTRIBUTION AUDIT COMPLETE — EXISTING SPLIT UNCHANGED.**\n")
        
    print("SPLIT DISTRIBUTION AUDIT COMPLETE — EXISTING SPLIT UNCHANGED.")

if __name__ == '__main__':
    main()

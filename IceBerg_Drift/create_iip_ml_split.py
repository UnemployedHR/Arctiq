import os
import json
import datetime
import pandas as pd
import numpy as np

def summarize_split(df):
    return {
        'count': len(df),
        'obs_mean': df['observation_count'].mean(),
        'obs_median': df['observation_count'].median(),
        'obs_min': df['observation_count'].min(),
        'obs_max': df['observation_count'].max(),
        'dur_mean': df['duration_hours'].mean(),
        'dur_median': df['duration_hours'].median(),
        'dur_min': df['duration_hours'].min(),
        'dur_max': df['duration_hours'].max(),
        'disp_mean': df['straight_line_displacement_km'].mean(),
        'disp_median': df['straight_line_displacement_km'].median(),
        'disp_min': df['straight_line_displacement_km'].min(),
        'disp_max': df['straight_line_displacement_km'].max()
    }

def format_stats(stats):
    return (
        f"- **Observation count:** Mean: {stats['obs_mean']:.2f}, Median: {stats['obs_median']:.2f}, "
        f"Min: {stats['obs_min']}, Max: {stats['obs_max']}\n"
        f"- **Duration (hours):** Mean: {stats['dur_mean']:.2f}, Median: {stats['dur_median']:.2f}, "
        f"Min: {stats['dur_min']:.2f}, Max: {stats['dur_max']:.2f}\n"
        f"- **Displacement (km):** Mean: {stats['disp_mean']:.2f}, Median: {stats['disp_median']:.2f}, "
        f"Min: {stats['disp_min']:.2f}, Max: {stats['disp_max']:.2f}\n"
    )

def main():
    SEED = 42
    
    catalog_path = 'data/iip/iip_2021_trajectory_catalog.csv'
    df = pd.read_csv(catalog_path)
    
    total_icebergs = len(df)
    
    # Stratification strategy from DATA_SPLIT_STRATEGY.md:
    # Stratify by duration bins (e.g., quartiles)
    df['duration_bin'] = pd.qcut(df['duration_hours'], q=4, labels=['short', 'medium', 'long', 'very_long'])
    
    # Custom stratified split using pandas
    np.random.seed(SEED)
    
    train_ids_list = []
    val_ids_list = []
    test_ids_list = []
    
    for bin_label, group in df.groupby('duration_bin', observed=True):
        group_ids = group['iceberg_number'].values.copy()
        np.random.shuffle(group_ids)
        
        n_total = len(group_ids)
        n_train = int(np.round(0.70 * n_total))
        n_val = int(np.round(0.15 * n_total))
        
        train_ids_list.extend(group_ids[:n_train])
        val_ids_list.extend(group_ids[n_train:n_train+n_val])
        test_ids_list.extend(group_ids[n_train+n_val:])
        
    train_df = df[df['iceberg_number'].isin(train_ids_list)].copy()
    val_df = df[df['iceberg_number'].isin(val_ids_list)].copy()
    test_df = df[df['iceberg_number'].isin(test_ids_list)].copy()
    
    # Cleanup temporary bin
    train_df = train_df.drop(columns=['duration_bin'])
    val_df = val_df.drop(columns=['duration_bin'])
    test_df = test_df.drop(columns=['duration_bin'])
    
    train_ids = set(train_df['iceberg_number'])
    val_ids = set(val_df['iceberg_number'])
    test_ids = set(test_df['iceberg_number'])
    all_original_ids = set(df['iceberg_number'])
    
    # -------------------------------------------------------------
    # 6. LEAKAGE VERIFICATION
    # -------------------------------------------------------------
    leakage = False
    if not train_ids.isdisjoint(val_ids):
        print("ERROR: Intersection between TRAIN and VALIDATION")
        leakage = True
    if not train_ids.isdisjoint(test_ids):
        print("ERROR: Intersection between TRAIN and TEST")
        leakage = True
    if not val_ids.isdisjoint(test_ids):
        print("ERROR: Intersection between VALIDATION and TEST")
        leakage = True
        
    union_ids = train_ids.union(val_ids).union(test_ids)
    if union_ids != all_original_ids:
        print("ERROR: The union of splits does not equal the catalog IDs")
        leakage = True
        
    if leakage:
        print("LEAKAGE VERIFICATION FAILED. STOPPING.")
        return
    else:
        print("Leakage verification passed: Sets are mutually exclusive and collectively exhaustive.")
        
    # -------------------------------------------------------------
    # 7. SPECIAL CHECK: 20857
    # -------------------------------------------------------------
    target_iceberg = 20857
    target_split = None
    if target_iceberg in train_ids:
        target_split = "TRAIN"
    elif target_iceberg in val_ids:
        target_split = "VALIDATION"
    elif target_iceberg in test_ids:
        target_split = "TEST"
    else:
        target_split = "NOT FOUND IN CATALOG"
        
    print(f"Iceberg 20857 is assigned to: {target_split}")
    
    # -------------------------------------------------------------
    # 4. OUTPUT
    # -------------------------------------------------------------
    out_dir = 'data/iip/ml_splits'
    os.makedirs(out_dir, exist_ok=True)
    
    train_df.to_csv(os.path.join(out_dir, 'train_icebergs.csv'), index=False)
    val_df.to_csv(os.path.join(out_dir, 'validation_icebergs.csv'), index=False)
    test_df.to_csv(os.path.join(out_dir, 'test_icebergs.csv'), index=False)
    
    manifest = {
        'random_seed': SEED,
        'split_ratio': '70-15-15',
        'creation_timestamp': datetime.datetime.now().isoformat(),
        'total_icebergs': total_icebergs,
        'train_count': len(train_df),
        'validation_count': len(val_df),
        'test_count': len(test_df),
        'train_percentage': len(train_df) / total_icebergs * 100,
        'validation_percentage': len(val_df) / total_icebergs * 100,
        'test_percentage': len(test_df) / total_icebergs * 100
    }
    
    with open(os.path.join(out_dir, 'iip_ml_split_manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=4)
        
    # -------------------------------------------------------------
    # 5. DATA DISTRIBUTION REPORT
    # -------------------------------------------------------------
    train_stats = summarize_split(train_df)
    val_stats = summarize_split(val_df)
    test_stats = summarize_split(test_df)
    
    report_path = 'ML_SPLIT_REPORT.md'
    with open(report_path, 'w') as f:
        f.write("# ML Data Split Distribution Report\n\n")
        f.write("## Overview\n")
        f.write(f"- **Total iceberg IDs:** {total_icebergs}\n")
        f.write(f"- **Train count:** {manifest['train_count']} ({manifest['train_percentage']:.2f}%)\n")
        f.write(f"- **Validation count:** {manifest['validation_count']} ({manifest['validation_percentage']:.2f}%)\n")
        f.write(f"- **Test count:** {manifest['test_count']} ({manifest['test_percentage']:.2f}%)\n\n")
        
        f.write("## TRAIN Set Statistics\n")
        f.write(format_stats(train_stats) + "\n")
        
        f.write("## VALIDATION Set Statistics\n")
        f.write(format_stats(val_stats) + "\n")
        
        f.write("## TEST Set Statistics\n")
        f.write(format_stats(test_stats) + "\n")
        
    # Final console output
    print("\nIIP ML ICEBERG SPLIT CREATED SUCCESSFULLY")
    print(f"- Train count: {manifest['train_count']}")
    print(f"- Validation count: {manifest['validation_count']}")
    print(f"- Test count: {manifest['test_count']}")
    print(f"- Random seed: {SEED}")
    print(f"- Split containing iceberg 20857: {target_split}")
    print(f"- Leakage verification result: PASSED (mutually exclusive & collectively exhaustive)")

if __name__ == '__main__':
    main()

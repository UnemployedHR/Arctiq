# Data Split Strategy for Iceberg Trajectory ML Dataset

This document defines the final leakage-safe strategy for splitting the IIP iceberg trajectories into TRAIN, VALIDATION, and TEST sets. This is a methodology/design task only. No ML samples are generated, no model is trained, and no environmental data is modified.

---

## 1. Primary Rule: Splitting by Iceberg ID

The absolute primary rule of the dataset split is that it **MUST happen at the iceberg-ID level**. The exact same `iceberg_id` must never appear in more than one split (e.g., if iceberg 20857 is in TRAIN, no portion of its trajectory can exist in VALIDATION or TEST).

**Why random row-level splitting is invalid:**
Trajectory data is highly autocorrelated (time-series). If you extract overlapping sequences (e.g., samples generated every 12 hours from a 10-day trajectory) and perform a random row-level split, the model will see overlapping historical and future segments in both train and test sets. The model would effectively "learn" to interpolate between known adjacent points from the same iceberg rather than learning the generalized physical relationship between environmental forcing and drift. This leads to catastrophic data leakage and artificially inflated performance metrics.

---

## 2. Proposed Split Ratios

Two candidate split ratios were evaluated:

- **70% TRAIN / 15% VALIDATION / 15% TEST**
- **80% TRAIN / 10% VALIDATION / 10% TEST**

**Trade-offs:** 
The IIP 2021 catalog contains 1,215 icebergs with $\ge 2$ valid observations. However, filtering out icebergs with less than 48 hours of total duration (needed for 24h history + 24h future) and missing environmental data will significantly reduce the usable iceberg pool. 
- A 10% test set might contain too few distinct icebergs to provide a statistically significant evaluation of generalization, especially when examining edge-case shapes/sizes.
- A 15% test set provides a more robust holdout group, ensuring enough physical diversity in the evaluation set to trust the metrics, at the cost of slightly fewer training examples.

**Recommendation:** **70% TRAIN / 15% VALIDATION / 15% TEST**. Given that data augmentation (via sliding windows) will generate multiple samples per usable iceberg, the model should have sufficient sample volume. Preserving 15% for rigorous, unbiased testing is critical.

---

## 3. Stratification

Randomly splitting icebergs could theoretically result in an unbalanced dataset (e.g., all large, long-duration icebergs end up in the test set). 

**Candidate stratification dimensions:**
- Observation count
- Trajectory duration
- Displacement magnitude
- Iceberg `SIZE`
- Iceberg `SHAPE`

**Practical Approach:** Over-stratifying small datasets often leads to brittle logic or forces deterministic splits that lack true randomness. We recommend a **stratified shuffle split solely based on trajectory duration bins** (e.g., short, medium, long). Duration correlates strongly with observation count and displacement magnitude, ensuring all three sets receive a healthy mix of short-lived and long-lived iceberg tracks without overly complex multi-dimensional binning.

---

## 4. Randomization

The split must be strictly reproducible. If the script is run multiple times, the exact same icebergs must be assigned to the exact same sets to ensure consistency across different model training iterations and baseline comparisons.

**Definition:** 
A fixed random seed (e.g., `RANDOM_SEED = 42`) will be passed to the pseudo-random number generator or stratification function during the iceberg-ID split step.

---

## 5. Temporal Considerations

A purely random, stratified iceberg-level split ensures spatial and temporal diversity across the sets.

- **Primary Test Split:** A randomized split (by ID) means that training and test icebergs may come from overlapping calendar periods (e.g., a July iceberg in TRAIN and another July iceberg in TEST). This is acceptable and constitutes the primary evaluation protocol, testing whether the model generalizes to *unseen icebergs* under known seasonal conditions.
- **Optional Robustness Test:** See Section 12.

---

## 6. Trajectory Length Requirements

To satisfy the ML problem definition (24-hour historical input + 24-hour future prediction), a specific iceberg can only contribute usable ML samples if it meets strict trajectory requirements.

**Minimum Requirement:**
- The iceberg must have a continuous track (or interpolatable track within strict gap limits) spanning **at least 48 hours** total.
- It must have environmental data coverage (GLORYS/ERA5) for that exact temporal and spatial window.

*Note: The actual usable sample count per set cannot be determined until the environmental alignment and quality-filtering pipelines are fully executed. The 1,215 catalog count is an upper bound of raw IDs, not the final ML sample count.*

---

## 7. Data Leakage Checks

To mathematically guarantee no leakage occurred, the following set-intersection assertions must be verified programmatically immediately after splitting:

1. `set(train_icebergs) ∩ set(validation_icebergs)` **must be empty.**
2. `set(train_icebergs) ∩ set(test_icebergs)` **must be empty.**
3. `set(validation_icebergs) ∩ set(test_icebergs)` **must be empty.**

Additionally, the final sequence generator must verify that no single iceberg ID appears in multiple generated dataset partitions (e.g., no `X_train` row shares an `iceberg_id` with an `X_test` row).

---

## 8. Sample Generation Order

To strictly enforce leakage prevention, the sequence extraction must follow this exact order:

1. **RAW IIP**
   ↓
2. **Clean observations** (filter NaNs, duplicates)
   ↓
3. **Identify usable iceberg trajectories** (filter by duration/gaps)
   ↓
4. **SPLIT BY ICEBERG ID** (assign to Train/Val/Test lists)
   ↓
5. **Generate training sequences separately**
   ↓
6. **Generate validation sequences separately**
   ↓
7. **Generate test sequences separately**

**Danger of Splitting After Sequence Generation:** If sequences are generated first, interpolation bounds, rolling averages, or min/max clipping could inadvertently blend information across what should be the train/test boundary. Splitting IDs *first* completely isolates the temporal contexts.

---

## 9. Normalization Leakage

All normalization parameters (scalers, normalizers, feature-selection statistics, imputation medians) must be **fitted strictly and exclusively on the TRAINING data sequences**.

Validation and test sequences must be treated as unseen incoming data and transformed using the parameters learned from the training set. Allowing validation or test sets to influence the preprocessing parameters is a subtle but significant form of data leakage.

---

## 10. Test Set Protection

The **TEST** set is a highly protected resource that must remain untouched until all model development, tuning, and selection are complete.

- **TRAIN:** Used for model weight fitting and gradient descent.
- **VALIDATION:** Used iteratively for hyperparameter tuning, model selection, and early stopping.
- **TEST:** Used exactly once (or in a final automated pipeline) for the final, unbiased evaluation of the chosen model.

---

## 11. Multiple Experiments & Fair Comparison

Future experiments comparing different algorithms must all utilize the exact same frozen test iceberg set. 

For instance:
- Persistence baseline
- XGBoost
- LSTM
- Physics baseline (OpenBerg)
- Hybrid physics + ML

All must evaluate their final metrics on the identical **TEST** set sequences. This guarantees a true apples-to-apples comparison of displacement error metrics.

---

## 12. Robustness Test (Temporal Generalization)

An optional, secondary evaluation protocol is proposed for future implementation: a **TEMPORAL GENERALIZATION TEST**.

Instead of a random split, the dataset is split chronologically (e.g., Train on early season May/June icebergs; Test on late season July/August icebergs). 
- **Utility:** Evaluates whether a model trained on spring environmental forcing (e.g., strong ocean currents, melting sea ice limits) degrades when predicting late-summer conditions. This simulates true operational deployment where a model must predict future, unseen seasons.

---

## 13. Final Recommendation

- **Recommended split ratio:** 70% TRAIN / 15% VALIDATION / 15% TEST
- **Random seed:** 42
- **Split unit:** `iceberg_id`
- **Minimum trajectory requirement:** $\ge 48$ hours total duration
- **Leakage checks:** Strict set-intersection assertions on IDs
- **Normalization strategy:** `fit()` on TRAIN only; `transform()` on VAL/TEST
- **Primary evaluation protocol:** Stratified random split by ID (binned by duration)
- **Optional temporal robustness protocol:** Future chronological split (e.g., test on late-season icebergs)

---
DATA SPLIT STRATEGY COMPLETE — NO FINAL SPLIT GENERATED.

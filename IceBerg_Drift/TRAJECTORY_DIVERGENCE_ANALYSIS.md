# Trajectory Divergence Analysis

## Position & Error Table
| Timestamp | Obs Lat | Obs Lon | Case A Lat | Case A Lon | Case A Err (km) | Case B Lat | Case B Lon | Case B Err (km) |
|-----------|---------|---------|------------|------------|-----------------|------------|------------|-----------------|
| 2021-06-02 16:41:00 | 59.4267 | -62.4100 | 59.4267 | -62.4100 | 0.00 | 59.4267 | -62.4100 | 0.00 |
| 2021-06-09 21:59:00 | 59.4050 | -62.1150 | 59.5212 | -62.5944 | 30.01 | 59.6561 | -62.4099 | 32.50 |

## Bearing & Forcing Table
| Timestamp | Obs Bear | Case A Bear | Case B Bear | Ocean Speed (m/s) | Ocean Dir | Wind Speed (m/s) | Wind Dir |
|-----------|----------|-------------|-------------|-------------------|-----------|------------------|----------|
| 2021-06-02 16:41:00 | N/A | N/A | N/A | 0.097 | 103.1 | 5.57 | 93.5 |
| 2021-06-09 21:59:00 | 98.1 | 315.4 | 0.0 | 0.118 | 146.5 | 7.34 | 138.2 |

## Conclusions
1. **First divergence time for Case A (>10km error):** 2021-06-09 21:59:00
2. **First divergence time for Case B (>10km error):** 2021-06-09 21:59:00
3. **Error at divergence points:** Case A: 30.01 km | Case B: 32.50 km
4. **Observed vs Modeled Movement Direction:**
   - At 2021-06-09 21:59:00, OBSERVED bearing was 98.1 while Case A was 315.4 and Case B was 0.0.
5. **Environmental Forcing at those points:**
   - At 2021-06-09 21:59:00, Ocean was 0.118 m/s towards 146.5 deg. Wind was 7.34 m/s towards 138.2 deg.
6. **Evidence-Supported Interpretation:**
   - **OBSERVED:** Both Case A and Case B drift significantly off the observed track at the very first measurable interval after initialization.
   - **OBSERVED:** The simulated trajectories diverge predominantly to the North/North-West (315 deg / 0 deg), while the observed trajectory moved East/South-East (98.1 deg).
   - **OBSERVED:** The extracted environmental forcing is generally directed East/South-East (Ocean towards ~103-146 deg, Wind towards ~93-138 deg), which broadly aligns with the *observed* iceberg direction.
   - **INFERRED:** Since the forcing is towards the SE but the model iceberg moves NW/N, there is a fundamental mismatch in how the model is applying or calculating forces. The divergence occurs immediately after initialization and is not a consequence of reaching the coast.
7. **Unresolved Questions for Next Experiment:**
   - Are the `x_wind` and `y_wind` mapping conventions inverted in the OpenBerg physics engine, causing the iceberg to be pushed *against* the wind/current?
   - Is there a massive Coriolis or water-drag artifact in the OpenBerg configuration causing anomalous North/West acceleration?

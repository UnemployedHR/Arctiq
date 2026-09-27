# Grounding Diagnostic Report V2

## OBSERVED Statistics Table
| Case | Grounding Time | Last Lat | Last Lon | Dist Boundary (deg) | 10-step mean (km) | 10-step max (km) | Mean Wind 24h (m/s) | Mean Ocean 24h (m/s) | Mechanism |
|------|----------------|----------|----------|---------------------|-------------------|------------------|---------------------|----------------------|-----------|
| Case A | 2021-06-19 12:41:00 | 58.7112 | -62.8971 | 0.5129 | 1.04 | 1.51 | 2.44 | 0.11 | Coastline/landmask interaction |
| Case B | 2021-06-21 21:41:00 | 58.7331 | -62.9030 | 0.5070 | 1.18 | 2.02 | 3.33 | 0.03 | Coastline/landmask interaction |

## INFERRED Diagnoses
### Case A
- Grounding at 2021-06-19 12:41:00 after reaching (58.7112, -62.8971).
- **INFERRED:** Gradual movement was observed prior to grounding; no sudden numerical jump detected.
- **INFERRED:** Grounding appears to be a physical interaction with the modeled coastline/landmask, as it is far from domain boundaries.
### Case B
- Grounding at 2021-06-21 21:41:00 after reaching (58.7331, -62.9030).
- **INFERRED:** Gradual movement was observed prior to grounding; no sudden numerical jump detected.
- **INFERRED:** Grounding appears to be a physical interaction with the modeled coastline/landmask, as it is far from domain boundaries.

## UNKNOWN Factors
- Whether the real iceberg grounded or simply drifted differently cannot be determined from this isolated output.
- The true subsurface bathymetry vs the 3D GLORYS landmask granularity remains unverified here.

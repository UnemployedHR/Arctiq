# Forcing Attribution 7-Day Experiment - Iceberg 20857
> Generated: 2026-09-27 11:47

## 1. Experiment Setup

| Parameter | Value |
|---|---|
| Start position | lat=59.42667, lon=-62.41 |
| Start time | 2021-06-02 16:41:00 |
| End time | 2021-06-09 21:59:00 |
| Duration | 173.3 hours |
| Timestep | 1 hour |
| Draft / Length / Width / Sail | 90 / 100 / 30 / 10 m |
| Horizontal diffusivity | 100 m²/s (unchanged from historical run) |
| Coriolis | ON (default) |
| vertical_profile | False (surface-only GLORYS) |
| Coastline | default (stranding) |

**NOTE:** Only the environmental readers change across cases.
All physics parameters are identical to `historical_validation_v2.py`.

| Case | Ocean Reader | Wind Reader |
|---|---|---|
| CaseA_Full       | GLORYS surface | ERA5 u10/v10 |
| CaseB_OceanOnly  | GLORYS surface | None (fallback=0) |
| CaseC_WindOnly   | None (fallback=0) | ERA5 u10/v10 |

## 2. IIP Endpoint Reference

| | Value |
|---|---|
| June 9 IIP lat (OBSERVED) | 59.405 |
| June 9 IIP lon (OBSERVED) | -62.115 |
| Net displacement from start | 16.86 km |
| Net displacement bearing | 98.2° |

## 3. Endpoint Comparison Table

| Case | End lat | End lon | Error vs IIP (km) | dLat | dLon | Net disp (km) | Net bearing | Grounded | Ground time |
|---|---|---|---|---|---|---|---|---|---|
| CaseA_Full | 59.52121 | -62.59435 | 30.01 | +0.11621° | -0.47935° | 14.8 | 315.3° | False | None |
| CaseB_OceanOnly | 59.00784 | -62.19208 | 44.38 | -0.39716° | -0.07708° | 48.19 | 165.0° | False | None |
| CaseC_WindOnly | 59.86552 | -62.60091 | 58.04 | +0.46052° | -0.48591° | 49.96 | 347.7° | False | None |

## 4. Mean Environmental Forcing During Active Period

| Case | Mean wind spd (m/s) | Mean wind bearing | Mean ocean spd (m/s) | Mean ocean bearing |
|---|---|---|---|---|
| CaseA_Full | 5.304 | 18.0° | 0.0795 | 148.2° |
| CaseB_OceanOnly | 0.0 | NA° | 0.1134 | 133.4° |
| CaseC_WindOnly | 5.612 | 29.6° | 0.0 | NA° |

## 5. Stochastic Random-Walk Scale Estimates

Theoretical RMS: σ = √(2Dt),  D = 100 m²/s

| Duration | σ_rms (km) |
|---|---|
| 1 hour | 0.85 |
| 24 hours | 4.16 |
| 7 days | 11.00 |

> **CLASSIFICATION: THEORETICAL STOCHASTIC SCALE ESTIMATE.**
> Over 7 days, theoretical RMS diffusion displacement ≈ 11.0 km.
> The Full case endpoint error is 30.01 km.
> Random walk could contribute noise of order ±11.0 km but cannot produce
> a systematic directional offset of this magnitude without additional forcing.

## 6. Attribution Analysis

### OBSERVED facts

1. Full forcing (GLORYS+ERA5) endpoint error vs June 9 IIP: **30.01 km**.
   Model is +0.1162° latitude, -0.4793° longitude from IIP.
2. Ocean-only endpoint error: **44.38 km** (model at 59.00784, -62.19208).
3. Wind-only endpoint error: **58.04 km** (model at 59.86552, -62.60091).
4. IIP net displacement: 16.86 km at bearing 98.2°.
5. Full forcing net displacement: 14.8 km at bearing 315.3°.

### INFERRED

6. **Wind attribution:** Comparing Full vs Ocean-only endpoints isolates the wind contribution.
   Full error=30.01 km vs Ocean-only error=44.38 km.
   Delta = 14.37 km - this is the approximate
   wind-induced change in endpoint error.

7. **Ocean attribution:** Comparing Full vs Wind-only endpoints isolates the ocean contribution.
   Full error=30.01 km vs Wind-only error=58.04 km.
   Delta = 28.03 km.

8. **Interaction:** Full ≠ Ocean-only + Wind-only because the forces are non-linear
   (drag depends on relative velocity between iceberg and fluid). Their combined effect
   is not a simple sum. This interaction cannot be separated from available outputs alone.

### UNKNOWN

9. The true path of the iceberg between 2021-06-02 and 2021-06-09 is unknown.
   Only the start and end positions are real IIP observations.
10. Whether GLORYS or ERA5 correctly represent the local environment at this specific
    iceberg location during this period cannot be determined from model output alone.
11. The magnitude of iceberg dimension changes (melting, roll-over) during 7 days is unknown.

## 7. Answers to Required Questions

1. **Actual June 9 endpoint error (Full forcing):** 30.01 km
2. **Removing wind effect:** Ocean-only error = 44.38 km vs Full = 30.01 km.
   Difference = 14.37 km. Wind removal materially changes the endpoint.
3. **Removing ocean effect:** Wind-only error = 58.04 km vs Full = 30.01 km.
   Difference = 28.03 km. Ocean removal materially changes the endpoint.
4. **Closest to IIP endpoint:** CaseA_Full with error=30.01 km.
5. **Grounding through June 9:**
   - CaseA_Full: grounded=False (at None)
   - CaseB_OceanOnly: grounded=False (at None)
   - CaseC_WindOnly: grounded=False (at None)
6. **Wind-only vs Ocean-only displacement:** INFERRED from endpoint positions above.
7. **Wind forcing evidence:** INFERRED only. Cannot claim causation without higher-resolution obs.
8. **Ocean forcing evidence:** INFERRED only. Same caveat applies.
9. **Interaction evidence:** Non-linear force balance means wind+ocean interaction is real but
   not directly separable from these three runs alone.
10. **Fundamentally unknowable:** True intermediate trajectory; local sub-grid environment;
    iceberg geometry evolution during the 7-day period.

---
*No model parameters were modified. Only forcing readers were changed per-case.*
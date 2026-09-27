# OpenBerg Vector Sanity Test Report
**OpenDrift version:** 1.14.11
**OpenBerg source file:** C:\Users\SAMEER\OneDrive\Desktop\iceberg_project\venv\Lib\site-packages\opendrift\models\openberg.py
## OpenBerg Source Code Excerpt
```python
class OpenBerg(OpenDriftSimulation):

    ElementType = IcebergObj

    required_variables = {
        "x_sea_water_velocity": {"fallback": None, "profiles": True},
        "y_sea_water_velocity": {"fallback": None, "profiles": True},
        "sea_floor_depth_below_sea_level": {"fallback": 10000},
        'sea_surface_height': {'fallback': 0, 'important': False},
        "sea_surface_x_slope": {"fallback": 0, 'important': False},
        "sea_surface_y_slope": {"fallback": 0, 'important': False},
        "x_wind": {"fallback": None},
        "y_wind": {"fallback": None},
        # Since OpenBerg model is deterministic for given iceberg size,
        # (in contrast to the Leeway model), we use a default diffusivity
        # to yield some variability.
        "horizontal_diffusivity": {"fallback": 100, "important": False},
        "sea_surface_wave_significant_height": {"fallback": 0},
        "sea_surface_wave_from_direction": {"fallback": 0},
        "sea_surface_wave_stokes_drift_x_velocity": {"fallback": 0, 'important': False},
        "sea_surface_wave_stokes_drift_y_velocity": {"fallback": 0, 'important': False},
        "sea_water_temperature": {"fallback": 2, "profiles": True, 'important': False},
        "sea_water_salinity": {"fallback": 35, "profiles": True, 'important': False},
        "sea_ice_area_fraction": {"fallback": 0, 'important': False},
        "sea_ice_thickness": {"fallback": 0, 'important': False},
        "sea_ice_x_velocity": {"fallback": 0, "important": False},
        "sea_ice_y_velocity": {"fallback": 0, "important": False},
        "land_binary_mask": {"fallback": None},
    }


    def get_profile_masked(self, variable):
        """
        Apply a mask to extract data from the surface down to the iceberg's draft.
        """
        draft = self.elements.draft
        profile = self.environment_profiles[variable]
        z = self.environment_profiles["z"] 
        if profile.ndim == 1:
            profile = profile[np.newaxis, :]
        if z is None or (len(z) == 1 and z[0] is None):
            z = np.zeros(profile.shape[0])
        z = np.atleast_1d(z)
        if z.ndim == 1:
            z = z[:, np.newaxis] 
        draft = np.atleast_1d(draft)
        mask = draft[np.newaxis, :] < -z 
        if mask.shape[0] > 1:
            mask[np.argmax(mask, axis=0), np.arange(mask.shape[1])] = False
        assert profile.shape == mask.shape, f"Incompatible shapes: profile {profile.shape}, mask {mask.shape}"

        return np.ma.masked_array(profile, mask, fill_value=np.nan)


    def get_basal_env(self, variable):
        """ Get the basal layer of the variable for the icebergs """
        profile = self.get_profile_masked(variable)
        last = np.argmin(np.logical_not(profile.mask), axis=0) - 1
        return profile[last, np.arange(profile.shape[1])]


    # Configuration
    def __init__(self, *args, **kwargs):
        super(OpenBerg, self).__init__(*args, **kwargs)
        self._add_config({
            'drift:wave_rad':{
                'type': 'bool',
                'default': True,
                'description': 'If True, wave radiation force is added',
                'level': CONFIG_LEVEL_BASIC
            },
            'drift:stokes_drift':{
                'type': 'bool',
                'default': False,
                'description': 'If True, stokes drift force is added',
                'level': CONFIG_LEVEL_BASIC
            },
            'drift:coriolis':{
                'type': 'bool',
                'default': True,
                'description': 'If True, coriolis force is added',
                'level': CONFIG_LEVEL_BASIC,
            },
            'drift:sea_surface_slope':{
            'type': 'bool',
            'default': False,
            'description': 'If True, sea surface slope force is added',
            'level': CONFIG_LEVEL_BASIC,
            },
            'drift:vertical_profile':{
                'type': 'bool',
                'default': False,
                'description': 'If True, depth integrated currents are applied',
                'level': CONFIG_LEVEL_BASIC
            },
            'processes:grounding':{
                'type': 'bool',
                'default': True,
                'description': 'If True, grounding is enabled',
                'level': CONFIG_LEVEL_BASIC
            },
            'processes:roll_over':{
                'type': 'bool',
                'default': True,
                'description': 'If True, roll over is enabled',
                'level': CONFIG_LEVEL_BASIC
            },
            'processes:melting':{
                'type': 'bool',
                'default': False,
                'description': 'If True, melting is enabled',
                'level': CONFIG_LEVEL_BASIC
            },
            'melting:wave':{
                'type': 'bool',
                'default': True,
                'description': 'If True, melting due to wave erosion is enabled',
                'level
... (truncated)
```
## Test Results
| Test | Uo | Vo | Uw | Vw | Expected | Actual | dLon | dLat | Disp(km) | Bear | PASS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TEST 1: ZERO FORCING | 0 | 0 | 0 | 0 | NONE | NONE | 0.0000 | 0.0000 | 0.00 | N/A | **PASS** |
| TEST 2: EASTWARD OCEAN CURRENT | 0.1 | 0 | 0 | 0 | EAST | SOUTHEAST | 0.1353 | -0.0309 | 8.39 | 114.1 | **PASS** |
| TEST 3: WESTWARD OCEAN CURRENT | -0.1 | 0 | 0 | 0 | WEST | NORTHWEST | -0.1354 | 0.0309 | 8.39 | 294.2 | **PASS** |
| TEST 4: NORTHWARD OCEAN CURRENT | 0 | 0.1 | 0 | 0 | NORTH | NORTHEAST | 0.0607 | 0.0689 | 8.40 | 24.1 | **FAIL** |
| TEST 5: SOUTHWARD OCEAN CURRENT | 0 | -0.1 | 0 | 0 | SOUTH | SOUTHWEST | -0.0606 | -0.0690 | 8.40 | 204.1 | **FAIL** |
| TEST 6: SOUTHEASTWARD OCEAN CURRENT | 0.1 | -0.1 | 0 | 0 | SOUTHEAST | SOUTH | 0.0768 | -0.0993 | 11.87 | 158.5 | **PASS** |
| TEST 7: EASTWARD WIND ONLY | 0 | 0 | 5.0 | 0 | EAST | EAST | 0.2128 | -0.0336 | 12.61 | 107.2 | **PASS** |
| TEST 8: WESTWARD WIND ONLY | 0 | 0 | -5.0 | 0 | WEST | WEST | -0.2130 | 0.0336 | 12.61 | 287.3 | **PASS** |
| TEST 9: SOUTHEASTWARD WIND ONLY | 0 | 0 | 5.0 | -5.0 | SOUTHEAST | SOUTHEAST | 0.2044 | -0.1706 | 22.23 | 148.5 | **PASS** |

## Multi-depth Test (Surface only fallback check)
| TEST 10: VPROF TRUE (fallback) | 0.1 | 0 | 0 | 0 | EAST | SOUTHEAST | 0.1353 | -0.0309 | 8.39 | 114.1 | **PASS** |

**CONCLUSION:** ONE OR MORE VECTOR TESTS FAILED. There is a sign/direction discrepancy in the core OpenBerg implementation.

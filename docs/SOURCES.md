# Data sources and assumptions

Every number in the game is either verified against a source or marked ASSUMPTION.
Fill the Source column with a real link and set Status to `verified`. Do not invent citations.
Unverified rows are counted by `python scripts/ares_setup.py verify`, which warns until every row has a real source.

| Value | Where | Current | Status | Source |
|---|---|---|---|---|
| Oxygen use per crew member per sol | constants.ts `O2_KG_PER_CREW_SOL` | 0.84 kg | TODO verify | NASA Baseline Values and Assumptions Document (BVAD): TODO link |
| CO2 produced per crew member per sol | `CO2_KG_PER_CREW_SOL` | 1.0 kg | TODO verify | BVAD: TODO link |
| Drinking water per crew member per sol | `WATER_L_PER_CREW_SOL` | 2.5 L | TODO verify | BVAD: TODO link |
| Food energy per crew member per sol | `KCAL_PER_CREW_SOL` | 2500 kcal | TODO verify | BVAD: TODO link |
| Mars solar day | scenarios.ts `solSeconds` | 88,775 s | TODO verify | NASA Mars fact sheet: TODO link |
| Mars solar irradiance | `solarIrradianceWm2` | 590 W/m2 | TODO verify | NASA Mars fact sheet: TODO link |
| Mars surface radiation dose | `radiationMSvPerDay` | 0.67 mSv/day | TODO verify | Curiosity RAD measurements: TODO link |
| Moon surface radiation dose | `radiationMSvPerDay` | 1.37 mSv/day | TODO verify | Lunar surface dosimetry: TODO link |
| Lunar light/dark cycle | `dayCycleSec` | 29.53 days | TODO verify | NASA Moon fact sheet: TODO link |
| Mars and Moon ambient temperatures | `ambientDayK`, `ambientNightK` | simplified | ASSUMPTION | TODO link |
| Earth to Mars signal delay | `commDelayTicks` | scaled for gameplay | ASSUMPTION | Real one-way delay is minutes: TODO link |
| Earth to Moon signal delay | `commDelayTicks` | scaled for gameplay | ASSUMPTION | Real one-way delay is about 1.3 s: TODO link |
| Kilopower output range | scenarios.ts `nuclearKw` | 10 kW | TODO verify | NASA Kilopower project: TODO link |
| Regolith shielding attenuation | `SHIELD_MU_PER_CM` | 0.015 per cm | ASSUMPTION | Simplified exponential model |
| Hab volume, heat capacity, hull loss | constants.ts | gameplay values | ASSUMPTION | Tuned for gameplay |
| Device rates and loads | constants.ts | gameplay values | ASSUMPTION | Tuned for gameplay |
| Stoichiometry (electrolysis, Sabatier) | constants.ts | molar masses | verified | Standard chemistry; checked by tests/engine/physics.test.ts |

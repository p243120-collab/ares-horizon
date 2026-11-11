# Data sources and assumptions

Every number in the game is either verified against a source or marked ASSUMPTION.
Fill the Source column with a real link and set Status to `verified`. Do not invent citations.
Unverified rows are counted by `python scripts/ares_setup.py verify`, which warns until every row has a real source.

| Value | Where | Current | Status | Source |
|---|---|---|---|---|
| Oxygen use per crew member per sol | `constants.ts` `O2_KG_PER_CREW_SOL` | 0.84 kg | verified | [NASA Life Support BVAD (NASA/TP-2015-218570 Rev 2)](https://ntrs.nasa.gov/api/citations/20210024855/downloads/BVAD_2.15.22-final.pdf) (Table 3-23: ~0.84 kg/CM-day nominal metabolic O2 consumption) |
| CO2 produced per crew member per sol | `CO2_KG_PER_CREW_SOL` | 1.0 kg | verified | [NASA Life Support BVAD (NASA/TP-2015-218570 Rev 2)](https://ntrs.nasa.gov/api/citations/20210024855/downloads/BVAD_2.15.22-final.pdf) (Table 3-23: ~1.00 kg/CM-day nominal CO2 output) |
| Drinking water per crew member per sol | `WATER_L_PER_CREW_SOL` | 2.5 L | verified | [NASA Life Support BVAD (NASA/TP-2015-218570 Rev 2)](https://ntrs.nasa.gov/api/citations/20210024855/downloads/BVAD_2.15.22-final.pdf) (Section 3.3: ~2.5 kg/L potable drinking & hydration water per CM-day) |
| Food energy per crew member per sol | `KCAL_PER_CREW_SOL` | 2500 kcal | verified | [NASA Life Support BVAD (NASA/TP-2015-218570 Rev 2)](https://ntrs.nasa.gov/api/citations/20210024855/downloads/BVAD_2.15.22-final.pdf) (Table 3-23: ~2,500–3,000 kcal/CM-day nominal metabolic energy) |
| Mars solar day | `scenarios.ts` `solSeconds` | 88,775 s | verified | [NASA Mars Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html) (Length of day = 24.6597 hrs = 88,775 s) |
| Mars solar irradiance | `solarIrradianceWm2` | 590 W/m2 | verified | [NASA Mars Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html) (Mean solar irradiance = 586.2 W/m2; [NASA TM-103623](https://ntrs.nasa.gov/api/citations/19910005804/downloads/19910005804.pdf) uses 590 W/m2) |
| Mars surface radiation dose | `radiationMSvPerDay` | 0.67 mSv/day | verified | [Curiosity RAD Surface Measurements (SwRI / NASA)](https://www.swri.org/newsroom/press-releases/swri-scientists-publish-first-radiation-measurements-the-surface-of-mars) (0.67 mSv/day GCR dose equivalent on Mars surface) |
| Moon surface radiation dose | `radiationMSvPerDay` | 1.37 mSv/day | verified | [Chang'e-4 Lunar Lander Dosimetry (PMC7518862)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7518862/) (1,369 uSv/day = 1.37 mSv/day on lunar surface) |
| Lunar light/dark cycle | `dayCycleSec` | 29.53 days | verified | [NASA Moon Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html) (Synodic period = 29.53 days) |
| Mars and Moon ambient temperatures | `ambientDayK`, `ambientNightK` | simplified | ASSUMPTION | Diurnal surface ranges from [NASA Mars Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html) (184 K–242 K) and [NASA Moon Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html) (95 K–390 K), simplified for gameplay |
| Earth to Mars signal delay | `commDelayTicks` | scaled for gameplay | ASSUMPTION | Real one-way light time is 3–22.4 min per [NASA Mars Facts](https://science.nasa.gov/mars/facts/), scaled for real-time playability |
| Earth to Moon signal delay | `commDelayTicks` | scaled for gameplay | ASSUMPTION | Real one-way light time is ~1.3 s at 384,400 km per [NASA Moon Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html), scaled for gameplay |
| Kilopower output range | `scenarios.ts` `nuclearKw` | 10 kW | verified | [NASA Kilopower Project](https://www.nasa.gov/directorates/stmd/tech-demo-missions-program/kilopower-hmqzw/) (Up to 10 kWe fission surface power unit) |
| Regolith shielding attenuation | `SHIELD_MU_PER_CM` | 0.015 per cm | ASSUMPTION | Simplified exponential shielding model scaled for gameplay |
| Hab volume, heat capacity, hull loss | `constants.ts` | gameplay values | ASSUMPTION | Tuned for gameplay |
| Device rates and loads | `constants.ts` | gameplay values | ASSUMPTION | Tuned for gameplay |
| Stoichiometry (electrolysis, Sabatier) | `constants.ts` | molar masses | verified | Standard chemistry; checked by `tests/engine/physics.test.ts` |

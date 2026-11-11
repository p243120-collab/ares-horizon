import { T } from './constants.ts';
import { pCO2Kpa, pO2Kpa } from './telemetry.ts';
import type { SimulationState } from './types.ts';

/** Mission Control's diagnosis. Rule-based so it is deterministic and testable. */
export function diagnose(s: SimulationState): string {
  const battPct = (100 * s.power.batteryKwh) / s.power.batteryMaxKwh;
  const tankPct = s.eclss.o2TankKg / s.eclss.o2TankMaxKg;
  if (s.env.speActive && !s.controls.shelter)
    return 'Solar particle event in progress. Move the crew into the shelter now and add regolith shielding when it passes.';
  if (!s.controls.scrubber || pCO2Kpa(s) > T.co2HighKpa)
    return 'CO2 is the fastest killer. Keep the scrubber running and let the Sabatier reactor recover water when hydrogen allows.';
  if (battPct < 20)
    return 'Battery is low. Shed non-essential loads first: hydroponics, then Sabatier, then electrolysis.';
  if (s.thermal.habTempK < T.coldK + 4)
    return 'Cabin is getting cold. Close the radiator louvers and raise the heater limit, then watch battery drain.';
  if (s.thermal.habTempK > T.hotK - 4)
    return 'Cabin is getting hot. Open the radiator louvers and switch off heavy loads.';
  if (s.thermal.radiatorM2 < s.thermal.radiatorBaseM2 - 0.1)
    return 'Radiator area is reduced after the puncture. Send a repair crew when the cabin is stable.';
  if (s.power.dustCoverage > 0.4)
    return 'Dust on the solar arrays is costing you power. Clean the panels once the storm eases.';
  if (tankPct < 0.4 && !s.controls.electrolysis)
    return 'Oxygen reserve is falling. Run electrolysis while you have spare power and water.';
  if (s.eclss.waterL < 0.25 * s.eclss.waterMaxL)
    return 'Water is low. Keep the recycler on and run the Sabatier reactor to recover water from CO2.';
  if (pO2Kpa(s) < T.hypoxiaKpa + 2)
    return 'Oxygen pressure is dropping. Check the reserve tank and electrolysis.';
  return 'All systems look nominal from here. Keep an eye on power and the next weather forecast.';
}

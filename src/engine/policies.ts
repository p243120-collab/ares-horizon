import { pCO2Kpa } from './telemetry.ts';
import type { Action, SimulationState } from './types.ts';

/** A policy looks at the state and returns actions. Used by tests and the balance check. */
export type Policy = (s: Readonly<SimulationState>) => Action[];

/** Does nothing: the starting configuration runs unattended. */
export const idlePolicy: Policy = () => [];

/** Switches every life-support system off. Must always fail. */
export const sabotagePolicy: Policy = (s) =>
  (['scrubber', 'recycler', 'hydroponics'] as const)
    .filter((k) => s.controls[k])
    .map((k): Action => ({ type: 'SET_SYSTEM', system: k, on: false }));

/** A reasonable operator. Shows the game is winnable and teaches the intended trade-offs. */
export const competentPolicy: Policy = (s) => {
  const a: Action[] = [];
  const set = (system: 'electrolysis' | 'sabatier' | 'scrubber' | 'recycler' | 'hydroponics' | 'shelter', on: boolean) => {
    if (s.controls[system] !== on) a.push({ type: 'SET_SYSTEM', system, on });
  };
  const battPct = (100 * s.power.batteryKwh) / s.power.batteryMaxKwh;
  const tankPct = (100 * s.eclss.o2TankKg) / s.eclss.o2TankMaxKg;

  set('scrubber', true);
  set('recycler', true);
  set('shelter', s.env.speActive);

  // Shed loads when the battery is low, restore when it recovers.
  if (battPct < 35) {
    set('hydroponics', false);
    set('sabatier', false);
    set('electrolysis', false);
  } else if (battPct > 60) {
    set('hydroponics', true);
    set('electrolysis', tankPct < 90 && s.eclss.waterL > 60);
    set('sabatier', pCO2Kpa(s) > 0.05 && s.eclss.h2Kg > 0.1);
  }

  // Thermal control with the louvers.
  const T = s.thermal.habTempK;
  if (T < 291 && s.thermal.louverPct > 0) a.push({ type: 'SET_RADIATOR', louverPct: Math.max(0, s.thermal.louverPct - 5) });
  if (T > 297 && s.thermal.louverPct < 100) a.push({ type: 'SET_RADIATOR', louverPct: Math.min(100, s.thermal.louverPct + 5) });

  if (s.power.dustCoverage > 0.3 && !s.env.stormActive) a.push({ type: 'CLEAN_PANELS' });
  if (s.thermal.radiatorM2 < s.thermal.radiatorBaseM2 && !s.env.speActive) a.push({ type: 'REPAIR_RADIATOR' });
  if (s.shielding.regolithCm < 40 && !s.env.speActive && s.tick % 50 === 0) a.push({ type: 'ADD_SHIELDING' });
  return a;
};

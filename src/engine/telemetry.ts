import { HAB_VOLUME_M3, MOLAR_CO2, MOLAR_O2, R_GAS } from './constants.ts';
import type { SimulationState } from './types.ts';

export type Status = 'nominal' | 'warning' | 'critical';

export function pO2Kpa(s: SimulationState): number {
  return ((s.eclss.o2AtmKg / MOLAR_O2) * R_GAS * s.thermal.habTempK) / HAB_VOLUME_M3 / 1000;
}
export function pCO2Kpa(s: SimulationState): number {
  return ((s.eclss.co2Kg / MOLAR_CO2) * R_GAS * s.thermal.habTempK) / HAB_VOLUME_M3 / 1000;
}

export interface Telemetry {
  pO2Kpa: number;
  pCO2Kpa: number;
  netKw: number;
  batteryPct: number;
  o2TankPct: number;
  waterPct: number;
  foodDays: number;
  habTempK: number;
  avgHealth: number;
  avgStress: number;
  alive: number;
}

export function getTelemetry(s: SimulationState): Telemetry {
  const alive = s.crew.filter((c) => c.alive);
  const n = Math.max(1, s.crew.length);
  return {
    pO2Kpa: pO2Kpa(s),
    pCO2Kpa: pCO2Kpa(s),
    netKw: s.power.generationKw - s.power.loadKw,
    batteryPct: (100 * s.power.batteryKwh) / s.power.batteryMaxKwh,
    o2TankPct: (100 * s.eclss.o2TankKg) / s.eclss.o2TankMaxKg,
    waterPct: (100 * s.eclss.waterL) / s.eclss.waterMaxL,
    foodDays: alive.length ? s.food.kcal / (alive.length * 2500) : 0,
    habTempK: s.thermal.habTempK,
    avgHealth: s.crew.reduce((a, c) => a + c.health, 0) / n,
    avgStress: alive.length ? alive.reduce((a, c) => a + c.stress, 0) / alive.length : 100,
    alive: alive.length,
  };
}

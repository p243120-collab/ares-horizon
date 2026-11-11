import type { ScenarioConfig } from './types.ts';

/**
 * Scenario data. Numbers marked ASSUMPTION are gameplay-scaled and must be
 * checked against NASA sources and recorded in docs/SOURCES.md (task T09).
 * To add a scenario: add an object here and the UI picks it up automatically.
 */
export const SCENARIOS: ScenarioConfig[] = [
  {
    id: 'mars-dust-storm',
    title: 'The Martian Dust Winter',
    body: 'Mars',
    blurb: 'A global dust storm cuts sunlight by about 88%. Keep four astronauts alive until Sol 15.',
    solSeconds: 88775, // Mars solar day, about 24 h 39 m 35 s
    secondsPerSolReal: 60,
    targetSols: 15,
    dayCycleSec: 88775,
    daylightFraction: 0.5,
    phaseOffsetSec: 0,
    solarIrradianceWm2: 590, // ASSUMPTION: mean top-of-atmosphere value, verify
    ambientDayK: 240, // ASSUMPTION
    ambientNightK: 190, // ASSUMPTION
    radiationMSvPerDay: 0.67, // ASSUMPTION: roughly the measured Mars surface dose, verify
    dustDepositionPerSol: 0.005,
    dustDepositionStormPerSol: 0.06,
    commDelayTicks: 200, // gameplay-scaled; real one-way delay is minutes
    crewCount: 4,
    initial: {
      solarCapacityKw: 30,
      nuclearKw: 10,
      batteryKwh: 150,
      batteryMaxKwh: 150,
      o2TankKg: 25,
      o2TankMaxKg: 60,
      waterL: 300,
      waterMaxL: 500,
      kcal: 80000,
      radiatorM2: 40,
      louverPct: 40,
      heaterMaxKw: 10,
      regolithCm: 20,
      h2Kg: 0.5,
      cropHealth: 0.8,
    },
    events: {
      perSol: { DUST_STORM: 0, SOLAR_PARTICLE_EVENT: 0.08, MICROMETEORITE: 0.06, POWER_SURGE: 0.04 },
      scheduled: [{ atSol: 2, kind: 'DUST_STORM' }],
    },
  },
  {
    id: 'moon-lunar-night',
    title: 'Lunar Night at the South Pole Ridge',
    body: 'Moon',
    blurb: 'The Sun sets about five days in and stays down for the rest of the mission. Nuclear power and batteries carry you.',
    solSeconds: 86400,
    secondsPerSolReal: 60,
    targetSols: 15,
    dayCycleSec: 2551392, // 29.53 Earth days
    daylightFraction: 0.5, // about 354 hours of night
    phaseOffsetSec: 864000, // start 10 days into the lunar day
    solarIrradianceWm2: 1361,
    ambientDayK: 220, // ASSUMPTION: polar ridge, simplified
    ambientNightK: 100, // ASSUMPTION
    radiationMSvPerDay: 1.37, // ASSUMPTION: roughly the measured lunar surface dose, verify
    dustDepositionPerSol: 0.008,
    dustDepositionStormPerSol: 0.008,
    commDelayTicks: 20, // real one-way delay is about 1.3 s
    crewCount: 4,
    initial: {
      solarCapacityKw: 20,
      nuclearKw: 10,
      batteryKwh: 150,
      batteryMaxKwh: 150,
      o2TankKg: 25,
      o2TankMaxKg: 60,
      waterL: 300,
      waterMaxL: 500,
      kcal: 80000,
      radiatorM2: 40,
      louverPct: 40,
      heaterMaxKw: 10,
      regolithCm: 20,
      h2Kg: 0.5,
      cropHealth: 0.8,
    },
    events: {
      perSol: { DUST_STORM: 0, SOLAR_PARTICLE_EVENT: 0.1, MICROMETEORITE: 0.1, POWER_SURGE: 0.04 },
      scheduled: [{ atSol: 3, kind: 'SOLAR_PARTICLE_EVENT' }],
    },
  },
];

export function getScenario(id: string): ScenarioConfig {
  const s = SCENARIOS.find((x) => x.id === id);
  if (!s) throw new Error(`Unknown scenario: ${id}`);
  return s;
}

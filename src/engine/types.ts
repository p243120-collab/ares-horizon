export type EventKind = 'DUST_STORM' | 'SOLAR_PARTICLE_EVENT' | 'MICROMETEORITE' | 'POWER_SURGE';
export type SystemName = 'electrolysis' | 'sabatier' | 'scrubber' | 'recycler' | 'hydroponics' | 'shelter';
export type MissionStatus = 'ACTIVE' | 'SUCCESS' | 'FAILED';

export interface ScenarioConfig {
  id: string;
  title: string;
  body: 'Mars' | 'Moon';
  blurb: string;
  solSeconds: number; // length of one local day in simulated seconds
  secondsPerSolReal: number; // real seconds per sol at 1x speed
  targetSols: number;
  dayCycleSec: number; // length of the light/dark cycle
  daylightFraction: number;
  phaseOffsetSec: number; // where in the cycle the mission starts
  solarIrradianceWm2: number;
  ambientDayK: number;
  ambientNightK: number;
  radiationMSvPerDay: number;
  dustDepositionPerSol: number;
  dustDepositionStormPerSol: number;
  commDelayTicks: number; // gameplay-scaled one-way delay, see docs/SOURCES.md
  crewCount: number;
  initial: {
    solarCapacityKw: number;
    nuclearKw: number;
    batteryKwh: number;
    batteryMaxKwh: number;
    o2TankKg: number;
    o2TankMaxKg: number;
    waterL: number;
    waterMaxL: number;
    kcal: number;
    radiatorM2: number;
    louverPct: number;
    heaterMaxKw: number;
    regolithCm: number;
    h2Kg: number;
    cropHealth: number;
  };
  events: {
    perSol: Record<EventKind, number>;
    scheduled: { atSol: number; kind: EventKind }[];
  };
}

export interface CrewMember {
  id: string;
  name: string;
  role: 'Commander' | 'Engineer' | 'Medic' | 'Botanist';
  health: number;
  stress: number;
  doseMSv: number;
  resilience: number;
  alive: boolean;
}

export interface ActiveEvent {
  kind: EventKind;
  startedAtSimSec: number;
  endsAtSimSec: number;
}

export type CauseKind = 'EVENT' | 'ACTION' | 'CRISIS' | 'WARNING' | 'RECOVERY' | 'INFO';
export interface CauseEntry {
  simTimeSec: number;
  sol: number;
  kind: CauseKind;
  code: string;
  message: string;
}

export interface HistoryPoint {
  sol: number;
  batteryKwh: number;
  netKw: number;
  pO2Kpa: number;
  pCO2Kpa: number;
  habTempK: number;
  waterL: number;
  kcal: number;
  avgHealth: number;
  avgStress: number;
}

export interface EarthMessage {
  sol: number;
  text: string;
}

export interface Controls {
  electrolysis: boolean;
  sabatier: boolean;
  scrubber: boolean;
  recycler: boolean;
  hydroponics: boolean;
  shelter: boolean;
}

export interface SimulationState {
  scenarioId: string;
  seed: number;
  rngState: number;
  tick: number;
  simTimeSec: number;
  sol: number;
  status: MissionStatus;
  env: {
    sunFactor: number;
    ambientK: number;
    irradianceWm2: number;
    doseRateMSvPerDay: number;
    stormActive: boolean;
    speActive: boolean;
  };
  power: {
    solarCapacityKw: number;
    nuclearKw: number;
    batteryKwh: number;
    batteryMaxKwh: number;
    dustCoverage: number;
    solarKw: number;
    generationKw: number;
    loadKw: number;
    supplyRatio: number;
  };
  eclss: {
    o2AtmKg: number;
    o2TankKg: number;
    o2TankMaxKg: number;
    co2Kg: number;
    waterL: number;
    waterMaxL: number;
    h2Kg: number;
  };
  thermal: {
    habTempK: number;
    targetK: number;
    radiatorM2: number;
    radiatorBaseM2: number;
    louverPct: number;
    heaterKw: number;
    heaterMaxKw: number;
  };
  food: { kcal: number; cropHealth: number };
  shielding: { regolithCm: number };
  controls: Controls;
  crew: CrewMember[];
  events: ActiveEvent[];
  flags: Record<string, boolean>;
  causeLog: CauseEntry[];
  history: HistoryPoint[];
  nextHistorySimSec: number;
  scheduledDone: number[];
  earth: {
    pending: { deliverAtTick: number; text: string } | null;
    inbox: EarthMessage[];
  };
}

export type Action =
  | { type: 'SET_SYSTEM'; system: SystemName; on: boolean }
  | { type: 'SET_RADIATOR'; louverPct: number }
  | { type: 'SET_HEATER'; maxKw: number }
  | { type: 'CLEAN_PANELS' }
  | { type: 'ADD_SHIELDING' }
  | { type: 'REPAIR_RADIATOR' }
  | { type: 'REQUEST_EARTH_ADVICE' };

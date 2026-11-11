import { getScenario } from './scenarios.ts';
import type { CauseEntry, SimulationState } from './types.ts';

export interface CrisisChain {
  crisis: CauseEntry;
  causes: CauseEntry[];
  explanation: string;
}

export interface Debrief {
  outcome: 'SUCCESS' | 'FAILED' | 'ACTIVE';
  sols: number;
  score: number;
  survivors: number;
  crewSize: number;
  avgHealth: number;
  avgStress: number;
  peakDoseMSv: number;
  chains: CrisisChain[];
  lessons: string[];
}

/** Teaching text per crisis code: the "why" a student should take away. */
const EXPLANATIONS: Record<string, { why: string; lesson: string }> = {
  BATTERY_EMPTY: {
    why: 'Generation fell below demand and the battery ran dry, so every powered system slowed down at once.',
    lesson: 'Power is the root of the system: when it fails, life support, heating and crops all fail together. Shed non-essential loads before the battery is empty.',
  },
  LOW_O2: {
    why: 'Oxygen is consumed by the crew every sol. When the reserve tank empties, the cabin pressure of oxygen falls.',
    lesson: 'Electrolysis turns water and electricity into oxygen, so oxygen depends on both water and power.',
  },
  HIGH_CO2: {
    why: 'Crew breathe out carbon dioxide continuously. Without the scrubber (or Sabatier reactor) it builds up in the cabin.',
    lesson: 'Carbon dioxide builds up fast and is dangerous at low levels. The scrubber needs power, so a power shortage becomes an air problem.',
  },
  COLD: {
    why: 'The cabin loses heat to space through the hull and radiators. Low power meant less equipment heat and a weaker heater.',
    lesson: 'Thermal control is a balance: close the radiator louvers to keep heat in, but the heater draws battery power.',
  },
  HOT: {
    why: 'Equipment heat built up faster than the radiators could remove it.',
    lesson: 'Heat has to go somewhere. Open the radiator louvers or switch off heavy loads.',
  },
  NO_WATER: {
    why: 'Water is used for drinking, crops and electrolysis, and only partly recovered.',
    lesson: 'Water is a closed loop. The recycler and the Sabatier reactor recover it, and both need power.',
  },
  NO_FOOD: {
    why: 'The pantry ran out because hydroponics produced too little (it needs power, water and a warm cabin).',
    lesson: 'Growing food competes with other systems for power and water. Decide early how much to rely on crops.',
  },
  HIGH_RADIATION: {
    why: 'A solar particle event sent a burst of radiation through the shielding.',
    lesson: 'Shielding thickness reduces dose exponentially, and sheltering cuts it further. Build shielding before the storm, not during it.',
  },
};

export function computeScore(s: SimulationState): number {
  const n = Math.max(1, s.crew.length);
  const alive = s.crew.filter((c) => c.alive);
  const avgHealth = s.crew.reduce((a, c) => a + c.health, 0) / n;
  const avgStress = alive.length ? alive.reduce((a, c) => a + c.stress, 0) / alive.length : 100;
  const raw = 0.5 * (alive.length / n) + 0.3 * (avgHealth / 100) + 0.2 * (1 - avgStress / 100);
  return Math.round(100 * Math.max(0, Math.min(1, raw)));
}

export function buildDebrief(s: SimulationState): Debrief {
  const sc = getScenario(s.scenarioId);
  const lookback = 1.5 * sc.solSeconds;
  const crises = s.causeLog.filter((e) => e.kind === 'CRISIS' && EXPLANATIONS[e.code]);
  const chains: CrisisChain[] = crises.map((crisis) => {
    const causes = s.causeLog.filter(
      (e) =>
        e.simTimeSec <= crisis.simTimeSec &&
        e.simTimeSec >= crisis.simTimeSec - lookback &&
        e !== crisis &&
        (e.kind === 'EVENT' || e.kind === 'ACTION' || e.kind === 'WARNING' || (e.kind === 'CRISIS' && e.code !== crisis.code)),
    );
    return { crisis, causes: causes.slice(-5), explanation: EXPLANATIONS[crisis.code].why };
  });
  const codes = Array.from(new Set(crises.map((c) => c.code)));
  const lessons = codes.map((c) => EXPLANATIONS[c].lesson);
  const alive = s.crew.filter((c) => c.alive);
  const n = Math.max(1, s.crew.length);
  return {
    outcome: s.status,
    sols: s.sol,
    score: computeScore(s),
    survivors: alive.length,
    crewSize: s.crew.length,
    avgHealth: s.crew.reduce((a, c) => a + c.health, 0) / n,
    avgStress: alive.length ? alive.reduce((a, c) => a + c.stress, 0) / alive.length : 100,
    peakDoseMSv: Math.max(0, ...s.crew.map((c) => c.doseMSv)),
    chains,
    lessons: lessons.length ? lessons : ['No crises this run. Try the harder scenario or a new seed.'],
  };
}

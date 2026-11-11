import type { Debrief } from '../engine/debrief.ts';
import type { SimulationState } from '../engine/types.ts';

const SAVE_KEY = 'ares-horizon:save';
const RUNS_KEY = 'ares-horizon:runs';

export interface RunSummary {
  scenarioId: string;
  seed: number;
  outcome: string;
  sols: number;
  score: number;
  survivors: number;
  at: string;
}

function safeGet(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}
function safeSet(key: string, value: string): void {
  try { localStorage.setItem(key, value); } catch { /* storage may be blocked: ignore */ }
}

export function saveGame(s: SimulationState): void { safeSet(SAVE_KEY, JSON.stringify(s)); }
export function loadGame(): SimulationState | null {
  const raw = safeGet(SAVE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw) as SimulationState; } catch { return null; }
}
export function clearGame(): void { try { localStorage.removeItem(SAVE_KEY); } catch { /* ignore */ } }

export function loadRuns(): RunSummary[] {
  const raw = safeGet(RUNS_KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) as RunSummary[]; } catch { return []; }
}
export function saveRun(s: SimulationState, d: Debrief): void {
  const runs = loadRuns();
  runs.unshift({ scenarioId: s.scenarioId, seed: s.seed, outcome: d.outcome, sols: d.sols, score: d.score, survivors: d.survivors, at: new Date().toISOString() });
  safeSet(RUNS_KEY, JSON.stringify(runs.slice(0, 20)));
}

/** Downloads the full run (state, cause log, history, debrief) as JSON for classroom debriefs. */
export function exportRun(s: SimulationState, d: Debrief): void {
  const blob = new Blob([JSON.stringify({ debrief: d, state: s }, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ares-horizon-${s.scenarioId}-seed${s.seed}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

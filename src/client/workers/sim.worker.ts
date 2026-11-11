/**
 * Runs the simulation off the main thread so the HUD stays smooth and the
 * clock keeps running when the tab is in the background.
 */
import { TICK_HZ } from '../../engine/constants.ts';
import { SimulationEngine } from '../../engine/SimulationEngine.ts';
import type { Action, SimulationState } from '../../engine/types.ts';

type InMsg =
  | { type: 'init'; scenarioId: string; seed: number; restore?: SimulationState }
  | { type: 'action'; action: Action }
  | { type: 'speed'; speed: number }
  | { type: 'stop' };

const ctx = self as unknown as {
  postMessage(m: unknown): void;
  onmessage: ((e: MessageEvent<InMsg>) => void) | null;
};

const TICK_MS = 1000 / TICK_HZ;
let engine: SimulationEngine | null = null;
let speed = 1;
let acc = 0;
let last = 0;
let timer: ReturnType<typeof setInterval> | null = null;

function post(): void {
  if (engine) ctx.postMessage({ type: 'state', state: engine.getState() });
}

function loop(): void {
  if (!engine) return;
  const now = performance.now();
  acc += (now - last) * speed;
  last = now;
  let n = Math.min(Math.floor(acc / TICK_MS), 200); // cap catch-up after a long stall
  acc = n > 0 ? acc - n * TICK_MS : acc;
  if (acc > 10 * TICK_MS) acc = 0;
  const wasActive = engine.peek().status === 'ACTIVE';
  while (n-- > 0 && engine.peek().status === 'ACTIVE') engine.step();
  if (speed > 0 && wasActive) post();
}

ctx.onmessage = (e) => {
  const m = e.data;
  if (m.type === 'init') {
    engine = new SimulationEngine(m.scenarioId, m.seed, m.restore);
    speed = 1;
    acc = 0;
    last = performance.now();
    if (timer) clearInterval(timer);
    timer = setInterval(loop, TICK_MS);
    post();
  } else if (m.type === 'action') {
    engine?.dispatch(m.action);
    post();
  } else if (m.type === 'speed') {
    speed = Math.max(0, m.speed);
    last = performance.now();
    post();
  } else if (m.type === 'stop') {
    if (timer) clearInterval(timer);
    timer = null;
    engine = null;
  }
};

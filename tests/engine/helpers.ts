import { SimulationEngine } from '../../src/engine/SimulationEngine.ts';
import type { Policy } from '../../src/engine/policies.ts';

/** Runs a mission to the end (or a tick limit) with an optional policy. */
export function runMission(scenarioId: string, seed: number, policy?: Policy, maxTicks = 20000): SimulationEngine {
  const e = new SimulationEngine(scenarioId, seed);
  let n = 0;
  while (e.peek().status === 'ACTIVE' && n++ < maxTicks) {
    if (policy) for (const a of policy(e.peek())) e.dispatch(a);
    e.step();
  }
  return e;
}

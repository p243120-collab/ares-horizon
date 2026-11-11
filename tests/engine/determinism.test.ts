import { describe, expect, it } from 'vitest';
import { SimulationEngine } from '../../src/engine/SimulationEngine.ts';
import { competentPolicy } from '../../src/engine/policies.ts';
import { runMission } from './helpers.ts';

describe('determinism', () => {
  it('same scenario, seed and policy give identical results', () => {
    const a = runMission('mars-dust-storm', 7, competentPolicy).getState();
    const b = runMission('mars-dust-storm', 7, competentPolicy).getState();
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });

  it('different seeds give different runs', () => {
    const a = runMission('mars-dust-storm', 1, competentPolicy).getState();
    const b = runMission('mars-dust-storm', 2, competentPolicy).getState();
    expect(JSON.stringify(a)).not.toEqual(JSON.stringify(b));
  });

  it('save and restore continues exactly like an uninterrupted run', () => {
    const full = new SimulationEngine('moon-lunar-night', 3);
    const half = new SimulationEngine('moon-lunar-night', 3);
    for (let i = 0; i < 1500; i++) { full.step(); half.step(); }
    const restored = new SimulationEngine('moon-lunar-night', 3, half.getState());
    for (let i = 0; i < 1500; i++) { full.step(); restored.step(); }
    expect(JSON.stringify(restored.getState())).toBe(JSON.stringify(full.getState()));
  });
});

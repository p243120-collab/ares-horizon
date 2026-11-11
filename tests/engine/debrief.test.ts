import { describe, expect, it } from 'vitest';
import { buildDebrief } from '../../src/engine/debrief.ts';
import { idlePolicy, sabotagePolicy } from '../../src/engine/policies.ts';
import { runMission } from './helpers.ts';

describe('debrief', () => {
  it('links crises to earlier causes and teaches a lesson', () => {
    const d = buildDebrief(runMission('mars-dust-storm', 4, sabotagePolicy).getState());
    expect(d.outcome).toBe('FAILED');
    expect(d.chains.length).toBeGreaterThan(0);
    expect(d.chains.some((c) => c.causes.length > 0)).toBe(true);
    expect(d.lessons.length).toBeGreaterThan(0);
    expect(d.score).toBeLessThan(40);
  });

  it('scores are between 0 and 100', () => {
    const d = buildDebrief(runMission('moon-lunar-night', 2, idlePolicy).getState());
    expect(d.score).toBeGreaterThanOrEqual(0);
    expect(d.score).toBeLessThanOrEqual(100);
  });
});

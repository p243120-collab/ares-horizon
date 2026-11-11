import { describe, expect, it } from 'vitest';
import { competentPolicy, idlePolicy, sabotagePolicy } from '../../src/engine/policies.ts';
import { SCENARIOS } from '../../src/engine/scenarios.ts';
import { runMission } from './helpers.ts';

const SEEDS = Array.from({ length: 12 }, (_, i) => i + 1);

describe.each(SCENARIOS.map((s) => s.id))('game balance: %s', (id) => {
  it('a competent operator almost always wins with most of the crew alive', () => {
    let wins = 0;
    let survivors = 0;
    for (const seed of SEEDS) {
      const s = runMission(id, seed, competentPolicy).peek();
      if (s.status === 'SUCCESS') wins++;
      survivors += s.crew.filter((c) => c.alive).length;
    }
    expect(wins).toBeGreaterThanOrEqual(SEEDS.length - 1);
    expect(survivors / SEEDS.length).toBeGreaterThanOrEqual(3.5);
  });

  it('doing nothing costs lives (the game is not trivially safe)', () => {
    let survivors = 0;
    for (const seed of SEEDS) survivors += runMission(id, seed, idlePolicy).peek().crew.filter((c) => c.alive).length;
    expect(survivors / SEEDS.length).toBeLessThan(3);
  });

  it('switching life support off always ends in failure', () => {
    for (const seed of SEEDS) expect(runMission(id, seed, sabotagePolicy).peek().status).toBe('FAILED');
  });
});

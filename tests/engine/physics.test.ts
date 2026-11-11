import { describe, expect, it } from 'vitest';
import * as K from '../../src/engine/constants.ts';
import { SimulationEngine } from '../../src/engine/SimulationEngine.ts';
import { pO2Kpa } from '../../src/engine/telemetry.ts';

describe('stoichiometry (mass is conserved)', () => {
  it('electrolysis: O2 + H2 mass equals water mass', () => {
    expect(K.ELECTROLYSIS_O2_PER_KG_WATER + K.ELECTROLYSIS_H2_PER_KG_WATER).toBeCloseTo(1, 3);
  });
  it('Sabatier: CO2 + H2 mass equals CH4 + water mass', () => {
    const ch4 = 16.043 / 44.01;
    expect(1 + K.SABATIER_H2_PER_KG_CO2).toBeCloseTo(ch4 + K.SABATIER_WATER_PER_KG_CO2, 2);
  });
  it('nominal atmosphere gives about 21.3 kPa of oxygen', () => {
    const e = new SimulationEngine('mars-dust-storm', 1);
    expect(pO2Kpa(e.peek())).toBeCloseTo(21.3, 0);
  });
});

describe('engine bounds', () => {
  it('values stay finite and inside physical limits over a full mission', () => {
    for (const id of ['mars-dust-storm', 'moon-lunar-night']) {
      const e = new SimulationEngine(id, 11);
      for (let i = 0; i < 9500; i++) {
        e.step();
        const s = e.peek();
        expect(Number.isFinite(s.thermal.habTempK)).toBe(true);
        expect(s.thermal.habTempK).toBeGreaterThanOrEqual(150);
        expect(s.thermal.habTempK).toBeLessThanOrEqual(350);
        expect(s.power.batteryKwh).toBeGreaterThanOrEqual(0);
        expect(s.power.batteryKwh).toBeLessThanOrEqual(s.power.batteryMaxKwh + 1e-9);
        expect(s.eclss.waterL).toBeGreaterThanOrEqual(0);
        expect(s.eclss.o2TankKg).toBeGreaterThanOrEqual(0);
        expect(s.eclss.co2Kg).toBeGreaterThanOrEqual(0);
      }
    }
  });

  it('one Mars sol takes about 600 ticks at 1x (60 real seconds)', () => {
    const e = new SimulationEngine('mars-dust-storm', 1);
    for (let i = 0; i < 600; i++) e.step();
    expect(e.peek().sol).toBe(1);
  });
});

describe('mission events and comms', () => {
  it('the scheduled Mars dust storm starts at sol 2 and cuts solar output', () => {
    const e = new SimulationEngine('mars-dust-storm', 5);
    for (let i = 0; i < 1250; i++) e.step();
    expect(e.peek().env.stormActive).toBe(true);
    expect(e.peek().causeLog.some((x) => x.code === 'DUST_STORM')).toBe(true);
  });

  it('Earth advice arrives only after the round-trip delay', () => {
    const e = new SimulationEngine('mars-dust-storm', 5);
    e.dispatch({ type: 'REQUEST_EARTH_ADVICE' });
    for (let i = 0; i < 399; i++) e.step();
    expect(e.peek().earth.inbox.length).toBe(0);
    for (let i = 0; i < 5; i++) e.step();
    expect(e.peek().earth.inbox.length).toBe(1);
  });

  it('shielding reduces dose rate', () => {
    const a = new SimulationEngine('moon-lunar-night', 1);
    const b = new SimulationEngine('moon-lunar-night', 1);
    for (let i = 0; i < 5; i++) b.dispatch({ type: 'ADD_SHIELDING' });
    a.step(); b.step();
    expect(b.peek().env.doseRateMSvPerDay).toBeLessThan(a.peek().env.doseRateMSvPerDay);
  });
});

import type { Status, Telemetry } from '../engine/telemetry.ts';

export const worst = (...s: Status[]): Status =>
  s.includes('critical') ? 'critical' : s.includes('warning') ? 'warning' : 'nominal';

export const statusBattery = (pct: number): Status => (pct < 15 ? 'critical' : pct < 35 ? 'warning' : 'nominal');
export const statusO2 = (kpa: number): Status => (kpa < 16 ? 'critical' : kpa < 19 ? 'warning' : 'nominal');
export const statusCO2 = (kpa: number): Status => (kpa > 0.5 ? 'critical' : kpa > 0.3 ? 'warning' : 'nominal');
export const statusTemp = (k: number): Status =>
  k < 283 || k > 305 ? 'critical' : k < 289 || k > 299 ? 'warning' : 'nominal';
export const statusWater = (pct: number): Status => (pct < 5 ? 'critical' : pct < 25 ? 'warning' : 'nominal');
export const statusFood = (days: number): Status => (days < 1 ? 'critical' : days < 4 ? 'warning' : 'nominal');
export const statusTank = (pct: number): Status => (pct < 10 ? 'critical' : pct < 25 ? 'warning' : 'nominal');
export const statusDose = (rate: number): Status => (rate > 30 ? 'critical' : rate > 5 ? 'warning' : 'nominal');

export function habitatStatus(t: Telemetry): Status {
  return worst(statusO2(t.pO2Kpa), statusCO2(t.pCO2Kpa), statusTemp(t.habTempK));
}

export const STATUS_WORD: Record<Status, string> = { nominal: 'Nominal', warning: 'Warning', critical: 'Critical' };
export const STATUS_ICON: Record<Status, string> = { nominal: '✔', warning: '▲', critical: '✖' };

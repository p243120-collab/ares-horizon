import type { SimulationState } from '../../engine/types.ts';
import { getTelemetry } from '../../engine/telemetry.ts';
import type { Status } from '../../engine/telemetry.ts';
import { STATUS_WORD, habitatStatus, statusBattery, statusTemp, worst } from '../status.ts';

interface Mod {
  id: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  status: Status;
  note: string;
}

/** Schematic of the outpost. Each module lights up with its live status. */
export function OutpostMap({ state }: { state: SimulationState }) {
  const t = getTelemetry(state);
  const f = state.flags;
  const mods: Mod[] = [
    {
      id: 'solar', label: 'Solar array', x: 14, y: 20, w: 92, h: 54,
      status: state.power.dustCoverage > 0.5 || state.env.stormActive ? 'warning' : 'nominal',
      note: state.env.stormActive ? 'Dust storm' : `${Math.round(state.power.dustCoverage * 100)}% dusty`,
    },
    {
      id: 'power', label: 'Power and battery', x: 14, y: 110, w: 92, h: 54,
      status: worst(statusBattery(t.batteryPct), f.BATTERY_EMPTY ? 'critical' : 'nominal'),
      note: `${t.batteryPct.toFixed(0)}% charge`,
    },
    {
      id: 'hab', label: 'Habitat', x: 150, y: 60, w: 110, h: 90,
      status: habitatStatus(t),
      note: `${t.alive} crew aboard`,
    },
    {
      id: 'life', label: 'Life support', x: 306, y: 14, w: 92, h: 54,
      status: f.LOW_O2 || f.HIGH_CO2 ? 'critical' : !state.controls.scrubber ? 'warning' : 'nominal',
      note: state.controls.scrubber ? 'Scrubber on' : 'Scrubber off',
    },
    {
      id: 'green', label: 'Greenhouse', x: 306, y: 94, w: 92, h: 54,
      status: f.NO_FOOD || f.NO_WATER ? 'critical' : !state.controls.hydroponics ? 'warning' : 'nominal',
      note: `Crops ${Math.round(state.food.cropHealth * 100)}%`,
    },
    {
      id: 'rad', label: 'Radiator', x: 306, y: 174, w: 92, h: 54,
      status: f.COLD || f.HOT ? statusTemp(t.habTempK) : state.thermal.radiatorM2 < state.thermal.radiatorBaseM2 - 0.1 ? 'warning' : 'nominal',
      note: `${state.thermal.louverPct}% open`,
    },
  ];
  const mid = (m: Mod) => ({ x: m.x + m.w / 2, y: m.y + m.h / 2 });
  const byId = Object.fromEntries(mods.map((m) => [m.id, m]));
  const link = (a: string, b: string, cls: string) => {
    const p = mid(byId[a]);
    const q = mid(byId[b]);
    return <line key={a + b} x1={p.x} y1={p.y} x2={q.x} y2={q.y} className={cls} />;
  };
  return (
    <svg viewBox="0 0 412 244" className="outpost-map" role="img" aria-label="Outpost schematic showing the status of each module">
      {link('solar', 'power', 'pipe pipe-power')}
      {link('power', 'hab', 'pipe pipe-power')}
      {link('hab', 'life', 'pipe pipe-air')}
      {link('hab', 'green', 'pipe pipe-bio')}
      {link('hab', 'rad', 'pipe pipe-heat')}
      {mods.map((m) => (
        <g key={m.id} className={`mod mod-${m.status}`} transform={`translate(${m.x} ${m.y})`}>
          <rect width={m.w} height={m.h} rx="6" />
          <text x={m.w / 2} y={m.h / 2 - 6} textAnchor="middle" className="mod-name">{m.label}</text>
          <text x={m.w / 2} y={m.h / 2 + 10} textAnchor="middle" className="mod-note">{m.note}</text>
          <text x={m.w / 2} y={m.h - 7} textAnchor="middle" className="mod-status">{STATUS_WORD[m.status]}</text>
        </g>
      ))}
    </svg>
  );
}

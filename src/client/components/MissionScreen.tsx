import { getScenario } from '../../engine/scenarios.ts';
import { getTelemetry } from '../../engine/telemetry.ts';
import type { Action, SimulationState } from '../../engine/types.ts';
import { Gauge, Sparkline } from './Gauge.tsx';
import { OutpostMap } from './OutpostMap.tsx';
import { ControlPanel, CrewPanel, LogPanel } from './Panels.tsx';
import { statusBattery, statusCO2, statusDose, statusFood, statusO2, statusTank, statusTemp, statusWater } from '../status.ts';

interface Props {
  state: SimulationState;
  speed: number;
  onSpeed: (v: number) => void;
  dispatch: (a: Action) => void;
  onQuit: () => void;
}

const SPEEDS: { label: string; v: number }[] = [
  { label: 'Pause', v: 0 },
  { label: '1x', v: 1 },
  { label: '2x', v: 2 },
  { label: '5x', v: 5 },
];

const EVENT_TEXT: Record<string, string> = {
  DUST_STORM: 'Dust storm: solar power is down',
  SOLAR_PARTICLE_EVENT: 'Solar particle event: shelter the crew',
};

export function MissionScreen({ state, speed, onSpeed, dispatch, onQuit }: Props) {
  const sc = getScenario(state.scenarioId);
  const t = getTelemetry(state);
  const progress = Math.min(100, (100 * state.simTimeSec) / (sc.targetSols * sc.solSeconds));
  const critical = Object.entries(state.flags).filter(([k, v]) => v && k !== 'O2_RESERVE_LOW').map(([k]) => k);
  const hist = state.history;
  const alarm = critical.length > 0 || state.env.speActive;
  const announce = state.causeLog.filter((e) => e.kind === 'CRISIS' || e.kind === 'EVENT').slice(-1)[0]?.message ?? '';
  const unit = sc.body === 'Mars' ? 'Sol' : 'Day';

  return (
    <div className={`mission ${alarm ? 'mission-alarm' : ''}`}>
      <header className="topbar">
        <div>
          <h1 className="topbar-title">{sc.title}</h1>
          <div className="muted small">{unit} {state.sol + 1} of {sc.targetSols}, seed {state.seed}</div>
        </div>
        <div className="progress" role="progressbar" aria-label="Mission progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress)}>
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="speed" role="group" aria-label="Simulation speed">
          {SPEEDS.map((s) => (
            <button key={s.label} type="button" aria-pressed={speed === s.v} onClick={() => onSpeed(s.v)}>{s.label}</button>
          ))}
        </div>
        <button type="button" className="ghost" onClick={onQuit}>Quit</button>
      </header>

      <div className="sr-only" aria-live="assertive" role="status">{announce}</div>

      {(critical.length > 0 || state.events.length > 0) && (
        <div className="alert-strip" role="group" aria-label="Active alerts">
          {state.events.map((e) => (
            <span key={e.kind} className="chip chip-warning">▲ {EVENT_TEXT[e.kind] ?? e.kind}</span>
          ))}
          {critical.map((c) => (
            <span key={c} className="chip chip-critical">✖ {c.replace(/_/g, ' ').toLowerCase()}</span>
          ))}
        </div>
      )}

      <div className="mission-grid">
        <div className="col">
          <section className="panel" aria-labelledby="map-h">
            <h2 id="map-h">Outpost</h2>
            <OutpostMap state={state} />
          </section>
          <CrewPanel state={state} />
          <ControlPanel state={state} dispatch={dispatch} />
        </div>
        <div className="col">
          <section className="panel" aria-labelledby="tel-h">
            <h2 id="tel-h">Telemetry</h2>
            <div className="gauge-grid">
              <Gauge label="Battery" value={t.batteryPct} min={0} max={100} unit="%" status={statusBattery(t.batteryPct)} digits={0}
                hint={`Makes ${state.power.generationKw.toFixed(1)} kW, uses ${state.power.loadKw.toFixed(1)} kW`} />
              <Gauge label="Oxygen pressure" value={t.pO2Kpa} min={0} max={25} unit="kPa" status={statusO2(t.pO2Kpa)} hint="Safe above 16 kPa" />
              <Gauge label="CO2 pressure" value={t.pCO2Kpa} min={0} max={1.5} unit="kPa" status={statusCO2(t.pCO2Kpa)} digits={2} hint="Safe below 0.5 kPa" />
              <Gauge label="Cabin temperature" value={t.habTempK} min={260} max={330} unit="K" status={statusTemp(t.habTempK)} digits={0}
                hint={`${(t.habTempK - 273.15).toFixed(0)} C, outside ${state.env.ambientK.toFixed(0)} K`} />
              <Gauge label="Oxygen reserve" value={t.o2TankPct} min={0} max={100} unit="%" status={statusTank(t.o2TankPct)} digits={0} />
              <Gauge label="Water" value={t.waterPct} min={0} max={100} unit="%" status={statusWater(t.waterPct)} digits={0} />
              <Gauge label="Food left" value={t.foodDays} min={0} max={30} unit="days" status={statusFood(t.foodDays)} digits={1} />
              <Gauge label="Radiation dose rate" value={state.env.doseRateMSvPerDay} min={0} max={60} unit="mSv/day" status={statusDose(state.env.doseRateMSvPerDay)} digits={1} />
            </div>
          </section>
          <section className="panel" aria-labelledby="trend-h">
            <h2 id="trend-h">Trends</h2>
            <div className="spark-grid">
              <Sparkline title="Battery" values={hist.map((h) => h.batteryKwh)} unit="kWh" digits={0} />
              <Sparkline title="Cabin temperature" values={hist.map((h) => h.habTempK)} unit="K" digits={0} />
              <Sparkline title="Oxygen pressure" values={hist.map((h) => h.pO2Kpa)} unit="kPa" />
              <Sparkline title="Crew health" values={hist.map((h) => h.avgHealth)} unit="%" digits={0} />
            </div>
          </section>
          <LogPanel state={state} dispatch={dispatch} />
        </div>
      </div>
    </div>
  );
}

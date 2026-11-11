import * as K from '../../engine/constants.ts';
import type { Action, SimulationState, SystemName } from '../../engine/types.ts';

type Dispatch = (a: Action) => void;

export function CrewPanel({ state }: { state: SimulationState }) {
  return (
    <section className="panel" aria-labelledby="crew-h">
      <h2 id="crew-h">Crew</h2>
      <ul className="crew-list">
        {state.crew.map((c) => (
          <li key={c.id} className={c.alive ? '' : 'crew-lost'}>
            <div className="crew-head">
              <strong>{c.name}</strong> <span className="muted">{c.role}</span>
            </div>
            {c.alive ? (
              <>
                <Bar label="Health" value={c.health} kind={c.health < 40 ? 'critical' : c.health < 70 ? 'warning' : 'nominal'} />
                <Bar label="Stress" value={c.stress} kind={c.stress > 70 ? 'critical' : c.stress > 45 ? 'warning' : 'nominal'} />
                <div className="muted small mono">Dose {c.doseMSv.toFixed(1)} mSv</div>
              </>
            ) : (
              <div className="small">Lost</div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function Bar({ label, value, kind }: { label: string; value: number; kind: string }) {
  return (
    <div className="bar-row">
      <span className="bar-label small">{label}</span>
      <div className="bar" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(value)}>
        <div className={`bar-fill bar-${kind}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
      </div>
      <span className="mono small">{Math.round(value)}</span>
    </div>
  );
}

const SYSTEMS: { id: SystemName; label: string; kw: number; what: string }[] = [
  { id: 'scrubber', label: 'CO2 scrubber', kw: K.LOAD_SCRUBBER_KW, what: 'Removes the CO2 the crew breathe out.' },
  { id: 'recycler', label: 'Water recycler', kw: K.LOAD_RECYCLER_KW, what: 'Recovers most of the water the crew use.' },
  { id: 'electrolysis', label: 'Electrolysis', kw: K.LOAD_ELECTROLYSIS_KW, what: 'Splits water into oxygen (reserve) and hydrogen.' },
  { id: 'sabatier', label: 'Sabatier reactor', kw: K.LOAD_SABATIER_KW, what: 'Turns CO2 and hydrogen back into water.' },
  { id: 'hydroponics', label: 'Hydroponics', kw: K.LOAD_HYDROPONICS_KW, what: 'Grows food and a little oxygen. Needs water and a warm cabin.' },
];

export function ControlPanel({ state, dispatch }: { state: SimulationState; dispatch: Dispatch }) {
  const damaged = state.thermal.radiatorM2 < state.thermal.radiatorBaseM2 - 0.1;
  return (
    <section className="panel" aria-labelledby="ctl-h">
      <h2 id="ctl-h">Systems</h2>
      <ul className="switch-list">
        {SYSTEMS.map((s) => (
          <li key={s.id}>
            <label className="switch-row">
              <input
                type="checkbox"
                role="switch"
                checked={state.controls[s.id]}
                onChange={(e) => dispatch({ type: 'SET_SYSTEM', system: s.id, on: e.target.checked })}
              />
              <span className="switch-text">
                <span>{s.label} <span className="mono muted small">{s.kw} kW</span></span>
                <span className="muted small">{s.what}</span>
              </span>
            </label>
          </li>
        ))}
        <li>
          <label className="switch-row">
            <input
              type="checkbox"
              role="switch"
              checked={state.controls.shelter}
              onChange={(e) => dispatch({ type: 'SET_SYSTEM', system: 'shelter', on: e.target.checked })}
            />
            <span className="switch-text">
              <span>Shelter in place</span>
              <span className="muted small">Cuts radiation dose to a quarter, but the crew get stressed.</span>
            </span>
          </label>
        </li>
      </ul>

      <div className="slider-row">
        <label htmlFor="louver">Radiator louvers <span className="mono">{state.thermal.louverPct}%</span></label>
        <input id="louver" type="range" min={0} max={100} step={5} value={state.thermal.louverPct}
          onChange={(e) => dispatch({ type: 'SET_RADIATOR', louverPct: Number(e.target.value) })} />
        <span className="muted small">Open to shed heat, close to keep it.</span>
      </div>
      <div className="slider-row">
        <label htmlFor="heater">Heater limit <span className="mono">{state.thermal.heaterMaxKw} kW</span></label>
        <input id="heater" type="range" min={0} max={15} step={1} value={state.thermal.heaterMaxKw}
          onChange={(e) => dispatch({ type: 'SET_HEATER', maxKw: Number(e.target.value) })} />
        <span className="muted small">The heater draws battery power when the cabin is cold.</span>
      </div>

      <div className="button-row">
        <button type="button" onClick={() => dispatch({ type: 'CLEAN_PANELS' })}>Clean solar panels</button>
        <button type="button" onClick={() => dispatch({ type: 'ADD_SHIELDING' })} disabled={state.shielding.regolithCm >= K.SHIELD_MAX_CM}>
          Add shielding ({state.shielding.regolithCm} cm)
        </button>
        <button type="button" onClick={() => dispatch({ type: 'REPAIR_RADIATOR' })} disabled={!damaged}>Repair radiator</button>
      </div>
    </section>
  );
}

export function LogPanel({ state, dispatch }: { state: SimulationState; dispatch: Dispatch }) {
  const recent = state.causeLog.slice(-10).reverse();
  const pending = state.earth.pending;
  return (
    <section className="panel" aria-labelledby="log-h">
      <h2 id="log-h">Mission log and Earth</h2>
      <div className="button-row">
        <button type="button" onClick={() => dispatch({ type: 'REQUEST_EARTH_ADVICE' })} disabled={!!pending}>
          {pending ? 'Waiting for Earth' : 'Ask Earth for advice'}
        </button>
      </div>
      {pending ? <p className="muted small">Signal delay: Earth will answer in about {Math.max(0, pending.deliverAtTick - state.tick) / K.TICK_HZ} seconds at 1x speed.</p> : null}
      {state.earth.inbox.length > 0 ? (
        <ul className="earth-list">
          {state.earth.inbox.slice(-3).reverse().map((m, i) => (
            <li key={i}><span className="mono small">Sol {m.sol}</span> {m.text}</li>
          ))}
        </ul>
      ) : null}
      <ol className="log-list">
        {recent.map((e, i) => (
          <li key={`${e.simTimeSec}-${i}`} className={`log-${e.kind.toLowerCase()}`}>
            <span className="mono small">Sol {e.sol}</span> {e.message}
          </li>
        ))}
      </ol>
    </section>
  );
}

import { useState } from 'react';
import { SCENARIOS } from '../../engine/scenarios.ts';
import type { SimulationState } from '../../engine/types.ts';
import { clearGame, loadGame, loadRuns } from '../persist.ts';

interface Props {
  onStart: (scenarioId: string, seed: number, restore?: SimulationState) => void;
}

export function SetupScreen({ onStart }: Props) {
  const [scenarioId, setScenarioId] = useState(SCENARIOS[0].id);
  const [seed, setSeed] = useState(() => Math.floor(Math.random() * 9000) + 1000);
  const [saved, setSaved] = useState(() => loadGame());
  const runs = loadRuns().slice(0, 5);
  const sc = SCENARIOS.find((s) => s.id === scenarioId) ?? SCENARIOS[0];

  return (
    <main className="setup">
      <header className="setup-head">
        <h1>Ares Horizon</h1>
        <p className="lead">
          Run a crewed outpost on Mars or the Moon. Power, air, water, heat and radiation all depend on each other, so
          every choice has a cost somewhere else.
        </p>
      </header>

      <fieldset className="scenario-list">
        <legend>Choose a mission</legend>
        {SCENARIOS.map((s) => (
          <label key={s.id} className={`scenario ${s.id === scenarioId ? 'scenario-on' : ''}`}>
            <input type="radio" name="scenario" value={s.id} checked={s.id === scenarioId} onChange={() => setScenarioId(s.id)} />
            <span>
              <strong>{s.title}</strong>
              <span className="muted"> on {s.body}</span>
              <span className="scenario-blurb">{s.blurb}</span>
            </span>
          </label>
        ))}
      </fieldset>

      <div className="setup-row">
        <label htmlFor="seed">Seed</label>
        <input id="seed" className="mono" type="number" value={seed} onChange={(e) => setSeed(Math.floor(Number(e.target.value)) || 1)} />
        <button type="button" className="ghost" onClick={() => setSeed(Math.floor(Math.random() * 9000) + 1000)}>Random</button>
        <span className="muted small">Same seed, same events. Share it so a whole class faces the same mission.</span>
      </div>

      <div className="button-row">
        <button type="button" className="primary" onClick={() => onStart(sc.id, seed)}>Start mission</button>
        {saved ? (
          <>
            <button type="button" onClick={() => onStart(saved.scenarioId, saved.seed, saved)}>
              Continue saved mission (Sol {saved.sol})
            </button>
            <button type="button" className="ghost" onClick={() => { clearGame(); setSaved(null); }}>Discard save</button>
          </>
        ) : null}
      </div>

      <section className="howto" aria-labelledby="how-h">
        <h2 id="how-h">How a mission works</h2>
        <p>
          One sol lasts about a minute at normal speed. Watch the gauges, keep the crew alive until Sol {sc.targetSols}, and
          use Ask Earth if you are stuck, but remember the reply is delayed. When the mission ends, the debrief traces every
          crisis back to its causes.
        </p>
      </section>

      {runs.length > 0 ? (
        <section aria-labelledby="runs-h">
          <h2 id="runs-h">Recent missions</h2>
          <ul className="runs">
            {runs.map((r, i) => (
              <li key={i} className="small">
                <span className="mono">{r.score}</span> points, {r.outcome === 'SUCCESS' ? 'completed' : 'failed'} on Sol {r.sols} with {r.survivors} survivors
                <span className="muted"> ({r.scenarioId}, seed {r.seed})</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}

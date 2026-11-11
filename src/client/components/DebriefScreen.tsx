import { buildDebrief } from '../../engine/debrief.ts';
import { getScenario } from '../../engine/scenarios.ts';
import type { SimulationState } from '../../engine/types.ts';
import { exportRun } from '../persist.ts';
import { Sparkline } from './Gauge.tsx';

interface Props {
  state: SimulationState;
  onAgain: () => void;
  onMenu: () => void;
}

export function DebriefScreen({ state, onAgain, onMenu }: Props) {
  const d = buildDebrief(state);
  const sc = getScenario(state.scenarioId);
  const ok = d.outcome === 'SUCCESS';
  const h = state.history;
  return (
    <main className="debrief">
      <header>
        <h1>{ok ? 'Mission complete' : 'Mission failed'}</h1>
        <p className="lead">
          {ok
            ? `${d.survivors} of ${d.crewSize} crew survived to the end of ${sc.title}.`
            : `The crew was lost on ${sc.body === 'Mars' ? 'Sol' : 'Day'} ${d.sols + 1} of ${sc.title}.`}{' '}
          Score <span className="mono">{d.score}</span> out of 100. Average stress {d.avgStress.toFixed(0)}, highest dose {d.peakDoseMSv.toFixed(1)} mSv.
        </p>
      </header>

      <section aria-labelledby="chains-h">
        <h2 id="chains-h">What went wrong, and why</h2>
        {d.chains.length === 0 ? (
          <p>No crises this run. Try the other mission or a new seed to meet different events.</p>
        ) : (
          <ol className="chains">
            {d.chains.map((c, i) => (
              <li key={i}>
                <h3>Sol {c.crisis.sol + 1}: {c.crisis.message}</h3>
                {c.causes.length > 0 ? (
                  <>
                    <p className="small muted">Earlier in the same stretch:</p>
                    <ul>
                      {c.causes.map((x, j) => (
                        <li key={j}><span className="mono small">Sol {x.sol + 1}</span> {x.message}</li>
                      ))}
                    </ul>
                  </>
                ) : null}
                <p>{c.explanation}</p>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section aria-labelledby="learn-h">
        <h2 id="learn-h">What to take away</h2>
        <ul>{d.lessons.map((l, i) => <li key={i}>{l}</li>)}</ul>
      </section>

      <section aria-labelledby="chart-h">
        <h2 id="chart-h">How the outpost changed</h2>
        <div className="spark-grid">
          <Sparkline title="Battery" values={h.map((x) => x.batteryKwh)} unit="kWh" digits={0} />
          <Sparkline title="Cabin temperature" values={h.map((x) => x.habTempK)} unit="K" digits={0} />
          <Sparkline title="Oxygen pressure" values={h.map((x) => x.pO2Kpa)} unit="kPa" />
          <Sparkline title="CO2 pressure" values={h.map((x) => x.pCO2Kpa)} unit="kPa" digits={2} />
          <Sparkline title="Water" values={h.map((x) => x.waterL)} unit="L" digits={0} />
          <Sparkline title="Crew health" values={h.map((x) => x.avgHealth)} unit="%" digits={0} />
        </div>
      </section>

      <div className="button-row">
        <button type="button" className="primary" onClick={onAgain}>Play this mission again</button>
        <button type="button" onClick={() => exportRun(state, d)}>Download run data</button>
        <button type="button" className="ghost" onClick={onMenu}>Back to menu</button>
      </div>
    </main>
  );
}

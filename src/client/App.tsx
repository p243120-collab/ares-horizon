import { useEffect, useRef } from 'react';
import { buildDebrief } from '../engine/debrief.ts';
import { DebriefScreen } from './components/DebriefScreen.tsx';
import { MissionScreen } from './components/MissionScreen.tsx';
import { SetupScreen } from './components/SetupScreen.tsx';
import { useSimulation } from './hooks/useSimulation.ts';
import { clearGame, saveRun } from './persist.ts';

export default function App() {
  const sim = useSimulation();
  const { state } = sim;
  const recorded = useRef(false);

  // Record the finished run once and clear the autosave.
  useEffect(() => {
    if (state && state.status !== 'ACTIVE' && !recorded.current) {
      recorded.current = true;
      saveRun(state, buildDebrief(state));
      clearGame();
    }
    if (state && state.status === 'ACTIVE') recorded.current = false;
  }, [state]);

  if (!state) return <SetupScreen onStart={sim.start} />;
  if (state.status !== 'ACTIVE') {
    return <DebriefScreen state={state} onAgain={() => sim.start(state.scenarioId, state.seed)} onMenu={sim.quit} />;
  }
  return <MissionScreen state={state} speed={sim.speed} onSpeed={sim.setSpeed} dispatch={sim.dispatch} onQuit={sim.quit} />;
}

import { useCallback, useEffect, useRef, useState } from 'react';
import type { Action, SimulationState } from '../../engine/types.ts';
import { saveGame } from '../persist.ts';

/** Owns the simulation Web Worker and exposes its latest state to React. */
export function useSimulation() {
  const worker = useRef<Worker | null>(null);
  const [state, setState] = useState<SimulationState | null>(null);
  const [speed, setSpeedState] = useState(1);
  const lastSavedSol = useRef(-1);

  const stop = useCallback(() => {
    worker.current?.postMessage({ type: 'stop' });
    worker.current?.terminate();
    worker.current = null;
  }, []);

  const start = useCallback(
    (scenarioId: string, seed: number, restore?: SimulationState) => {
      stop();
      lastSavedSol.current = -1;
      const w = new Worker(new URL('../workers/sim.worker.ts', import.meta.url), { type: 'module' });
      w.onmessage = (e: MessageEvent<{ type: 'state'; state: SimulationState }>) => setState(e.data.state);
      w.postMessage({ type: 'init', scenarioId, seed, restore });
      worker.current = w;
      setSpeedState(1);
    },
    [stop],
  );

  const dispatch = useCallback((action: Action) => {
    worker.current?.postMessage({ type: 'action', action });
  }, []);

  const setSpeed = useCallback((v: number) => {
    setSpeedState(v);
    worker.current?.postMessage({ type: 'speed', speed: v });
  }, []);

  const quit = useCallback(() => {
    stop();
    setState(null);
  }, [stop]);

  // Autosave once per sol, whatever the game speed.
  useEffect(() => {
    if (!state || state.status !== 'ACTIVE') return;
    if (state.sol !== lastSavedSol.current) {
      lastSavedSol.current = state.sol;
      saveGame(state);
    }
  }, [state]);

  useEffect(() => () => stop(), [stop]);

  return { state, speed, start, dispatch, setSpeed, quit };
}

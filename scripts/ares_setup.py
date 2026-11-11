#!/usr/bin/env python3
"""
ARES HORIZON: one-script setup, verification and AI-agent task runner.

Free tools only (Node.js, npm, git, GitHub Pages). No paid services, no API keys.

USAGE (run from any folder; Python 3.8+):

    python ares_setup.py all                 # scaffold + install + verify + git commit
    python ares_setup.py scaffold            # write the project files
    python ares_setup.py install             # npm install
    python ares_setup.py verify              # run every quality gate, write agent/verify-report.md
    python ares_setup.py dev                 # start the dev server
    python ares_setup.py tasks               # list the agent task queue and progress
    python ares_setup.py next                # print the next task as a ready-to-paste agent prompt
    python ares_setup.py done T04            # verify, check the task's own acceptance test, mark done
    python ares_setup.py status              # one-screen progress summary

OPTIONS:
    --dir PATH         project folder (default: ./ares-horizon)
    --blueprint FILE   your original blueprint .md, copied into docs/BLUEPRINT.md
    --force            overwrite an existing project folder (scaffold)

HOW AN AI AGENT USES THIS: read AGENTS.md, run `next`, do the task, run `done <ID>`, repeat
until `status` says every required task is done.

Prerequisites (all free): Node.js 18 or newer, npm, git, Python 3.8 or newer.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_NAME = "ares-horizon"
IS_WINDOWS = os.name == "nt"

# ---------------------------------------------------------------------------
# 1. PROJECT FILES (generated from a tested project; edit freely after scaffold)
# ---------------------------------------------------------------------------
FILES = {
    '.gitignore': r'''node_modules
dist
coverage
.vite
*.log
.env
.env.*
!.env.example
.DS_Store
__pycache__
''',
    'README.md': r'''# Ares Horizon

A browser game and simulation engine for running a crewed outpost on Mars or the Moon.
Power, air, water, heat, food and radiation depend on each other, so every decision has a cost somewhere else.
Built for the NASA Space Apps Challenge on crewed lunar and Martian outposts.

**Live demo:** (fill in: GitHub Pages link, task T03)

## What it does

- Coupled life-support model: solar and nuclear power, battery, CO2 scrubber, water recycler, electrolysis, Sabatier reactor, hydroponics, radiator louvers, heater, regolith shielding.
- Individual crew with health, stress and radiation dose.
- Seeded random events: dust storm, solar particle event, micrometeorite puncture, power surge. Same seed, same mission, so a whole class can face the same run.
- Delayed advice from Earth (the delay is scaled for gameplay).
- A debrief that traces each crisis back to its causes and explains the science.
- Two missions: The Martian Dust Winter, and Lunar Night at the South Pole Ridge.
- Runs entirely in the browser. No server, no accounts, free to host.

## Quick start

```bash
npm install
npm run dev        # play at the printed local address
npm test           # engine tests (physics, determinism, balance, debrief)
npm run build      # production build in dist/
```

Or use the automation script: `python scripts/ares_setup.py verify`.

## How it is built

```mermaid
flowchart LR
  UI[React HUD] <-- state and actions --> W[Web Worker]
  W --> E[SimulationEngine]
  E --> D[Scenarios and constants]
  E --> L[Cause log]
  L --> B[Debrief builder]
  UI --> S[(localStorage save)]
```

The engine in `src/engine` is pure TypeScript with no DOM, so it is fast to test and easy to reason about.
See `docs/ARCHITECTURE.md` for the time-scaling maths and how to extend the game.

## Implemented and planned

| Area | Status |
|---|---|
| Deterministic engine, 2 scenarios, events, crew, debrief | Implemented |
| Unit, determinism and balance tests, CI | Implemented |
| Save, continue and JSON export of runs | Implemented |
| Verified and cited data (docs/SOURCES.md) | In progress |
| Pre/post learning quiz, tutorial | Planned |
| Classroom mode (free Supabase tier) | Planned |
| Isometric PixiJS map | Planned |

`docs/BLUEPRINT.md` holds the original enterprise design. It is the long-term roadmap, not what is built today.

## Honest limits

Rates and sizes are simplified for gameplay. Every value marked ASSUMPTION in `src/engine/constants.ts` and `scenarios.ts` is tracked in `docs/SOURCES.md` until it is verified against a NASA source.

## Team

(fill in: names, roles and what each person built, task T10)
''',
    'index.html': r'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Ares Horizon: run a crewed Mars or Moon outpost and learn how life support, power, heat and radiation depend on each other." />
    <title>Ares Horizon</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
''',
    'package.json': r'''{
  "name": "ares-horizon",
  "private": true,
  "version": "1.0.0",
  "description": "Crewed lunar and Martian outpost simulator for STEM learning (NASA Space Apps Challenge).",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.4",
    "vite": "^5.4.0",
    "vitest": "^2.0.5"
  }
}
''',
    'tsconfig.json': r'''{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "isolatedModules": true,
    "allowImportingTsExtensions": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "types": ["vite/client"]
  },
  "include": ["src", "tests", "vite.config.ts"]
}
''',
    'vite.config.ts': r'''import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// base './' lets the built site run from any sub-path (GitHub Pages project sites).
export default defineConfig({
  plugins: [react()],
  base: './',
  worker: { format: 'es' },
  test: { environment: 'node', include: ['tests/**/*.test.ts'] },
});
''',
    '.github/workflows/ci.yml': r'''name: CI

on:
  push:
    branches: [main]
  pull_request:

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: Typecheck, test and build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run typecheck
      - run: npm test
      - run: npm run build
''',
    '.github/workflows/pages.yml': r'''name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm test
      - run: npm run build
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
      - id: deployment
        uses: actions/deploy-pages@v4
''',
    'docs/ARCHITECTURE.md': r'''# Architecture

## Layers

| Layer | Folder | Rule |
|---|---|---|
| Engine | `src/engine` | Pure TypeScript. No DOM, no timers, no `Math.random`, no `Date`. |
| Worker | `src/client/workers` | Owns the clock. Calls `engine.step()` at 10 Hz, scaled by game speed. |
| Hook and persistence | `src/client/hooks`, `src/client/persist.ts` | Bridges worker and React. Saves to `localStorage` once per sol. |
| UI | `src/client/components` | Renders state. Sends `Action` objects. Holds no game rules. |

## Time scaling

One tick is 0.1 real seconds at 1x. Each tick covers `solSeconds / (secondsPerSolReal * 10)` simulated seconds.
For Mars that is 88,775 / 600, about 148 s per tick, split into 4 sub-steps so explicit Euler integration stays stable.
A mission of 15 sols therefore takes 15 real minutes at 1x, and the scenario's `secondsPerSolReal` changes this.

## Determinism

All randomness comes from `nextFloat(state)` (mulberry32). The random state is part of `SimulationState`, so a saved game continues exactly as an uninterrupted one. Tests enforce this.

## Coupling (why the game teaches something)

- Solar output depends on site, day or night, dust on the arrays and storms.
- Every system draws power. If the battery empties, supply drops below demand and all systems slow together.
- Electrolysis makes oxygen and hydrogen from water. The Sabatier reactor needs that hydrogen to turn CO2 back into water.
- Heat: equipment heat, heater, hull loss and the radiator (Stefan-Boltzmann, with adjustable louvers) set the cabin temperature. Hydroponics only grows in a warm cabin.
- Radiation dose falls exponentially with regolith thickness and drops further when the crew shelter.

## Extending

- New scenario: add an object to `SCENARIOS` in `src/engine/scenarios.ts`. The setup screen lists it automatically. Add it to the balance test run (it already loops over `SCENARIOS`).
- New system: add a control flag in `types.ts` and `createInitialState`, its load in `constants.ts`, its effect in `integrate()`, a toggle in `Panels.tsx`, and a test.
- New event: add to `EventKind`, handle in `startEvent`, add scenario rates, add a debrief explanation if it can cause a crisis.
- New crisis: add a check in `detectCrises` and an entry in `EXPLANATIONS` in `debrief.ts`.
''',
    'docs/PLAYTEST.md': r'''# Playtest log

Record every playtest session here (task T05 and T06). Do not record names. Use "Player 1", "Player 2".

| Player | Age group | Scenario and seed | Outcome | Score | Confusing moments | Quiz before | Quiz after |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Summary

- Players:
- Average score:
- Most common confusion:
- Changes made because of this:
''',
    'docs/SOURCES.md': r'''# Data sources and assumptions

Every number in the game is either verified against a source or marked ASSUMPTION.
Fill the Source column with a real link and set Status to `verified`. Do not invent citations.
Unverified rows are counted by `python scripts/ares_setup.py verify`, which warns until every row has a real source.

| Value | Where | Current | Status | Source |
|---|---|---|---|---|
| Oxygen use per crew member per sol | constants.ts `O2_KG_PER_CREW_SOL` | 0.84 kg | TODO verify | NASA Baseline Values and Assumptions Document (BVAD): TODO link |
| CO2 produced per crew member per sol | `CO2_KG_PER_CREW_SOL` | 1.0 kg | TODO verify | BVAD: TODO link |
| Drinking water per crew member per sol | `WATER_L_PER_CREW_SOL` | 2.5 L | TODO verify | BVAD: TODO link |
| Food energy per crew member per sol | `KCAL_PER_CREW_SOL` | 2500 kcal | TODO verify | BVAD: TODO link |
| Mars solar day | scenarios.ts `solSeconds` | 88,775 s | TODO verify | NASA Mars fact sheet: TODO link |
| Mars solar irradiance | `solarIrradianceWm2` | 590 W/m2 | TODO verify | NASA Mars fact sheet: TODO link |
| Mars surface radiation dose | `radiationMSvPerDay` | 0.67 mSv/day | TODO verify | Curiosity RAD measurements: TODO link |
| Moon surface radiation dose | `radiationMSvPerDay` | 1.37 mSv/day | TODO verify | Lunar surface dosimetry: TODO link |
| Lunar light/dark cycle | `dayCycleSec` | 29.53 days | TODO verify | NASA Moon fact sheet: TODO link |
| Mars and Moon ambient temperatures | `ambientDayK`, `ambientNightK` | simplified | ASSUMPTION | TODO link |
| Earth to Mars signal delay | `commDelayTicks` | scaled for gameplay | ASSUMPTION | Real one-way delay is minutes: TODO link |
| Earth to Moon signal delay | `commDelayTicks` | scaled for gameplay | ASSUMPTION | Real one-way delay is about 1.3 s: TODO link |
| Kilopower output range | scenarios.ts `nuclearKw` | 10 kW | TODO verify | NASA Kilopower project: TODO link |
| Regolith shielding attenuation | `SHIELD_MU_PER_CM` | 0.015 per cm | ASSUMPTION | Simplified exponential model |
| Hab volume, heat capacity, hull loss | constants.ts | gameplay values | ASSUMPTION | Tuned for gameplay |
| Device rates and loads | constants.ts | gameplay values | ASSUMPTION | Tuned for gameplay |
| Stoichiometry (electrolysis, Sabatier) | constants.ts | molar masses | verified | Standard chemistry; checked by tests/engine/physics.test.ts |
''',
    'src/client/App.tsx': r'''import { useEffect, useRef } from 'react';
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
''',
    'src/client/components/DebriefScreen.tsx': r'''import { buildDebrief } from '../../engine/debrief.ts';
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
''',
    'src/client/components/Gauge.tsx': r'''import type { Status } from '../../engine/telemetry.ts';
import { STATUS_ICON, STATUS_WORD } from '../status.ts';

interface GaugeProps {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  status: Status;
  digits?: number;
  hint?: string;
}

const ARC_LEN = Math.PI * 40;

/** Half-ring gauge. Colour is never the only signal: an icon and a status word are always shown. */
export function Gauge({ label, value, min, max, unit, status, digits = 1, hint }: GaugeProps) {
  const frac = Math.max(0, Math.min(1, (value - min) / (max - min)));
  return (
    <div className={`gauge gauge-${status}`} role="group" aria-label={`${label}: ${value.toFixed(digits)} ${unit}, ${STATUS_WORD[status]}`}>
      <svg viewBox="0 0 100 60" aria-hidden="true">
        <path d="M10 50 A40 40 0 0 1 90 50" className="gauge-track" />
        <path d="M10 50 A40 40 0 0 1 90 50" className="gauge-fill" strokeDasharray={`${frac * ARC_LEN} ${ARC_LEN}`} />
      </svg>
      <div className="gauge-value mono">
        {value.toFixed(digits)}
        <span className="gauge-unit"> {unit}</span>
      </div>
      <div className="gauge-label">{label}</div>
      <div className="gauge-status">
        <span aria-hidden="true">{STATUS_ICON[status]}</span> {STATUS_WORD[status]}
      </div>
      {hint ? <div className="gauge-hint">{hint}</div> : null}
    </div>
  );
}

interface SparkProps {
  title: string;
  values: number[];
  unit: string;
  digits?: number;
}

/** Minimal line chart with no dependencies. */
export function Sparkline({ title, values, unit, digits = 1 }: SparkProps) {
  const w = 220;
  const h = 56;
  if (values.length < 2) {
    return (
      <figure className="spark">
        <figcaption>{title}</figcaption>
        <div className="spark-empty">Collecting data</div>
      </figure>
    );
  }
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const span = hi - lo || 1;
  const pts = values.map((v, i) => `${((i / (values.length - 1)) * w).toFixed(1)},${(h - 4 - ((v - lo) / span) * (h - 8)).toFixed(1)}`).join(' ');
  return (
    <figure className="spark">
      <figcaption>
        {title} <span className="mono muted">{lo.toFixed(digits)} to {hi.toFixed(digits)} {unit}</span>
      </figcaption>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${title} over time, from ${lo.toFixed(digits)} to ${hi.toFixed(digits)} ${unit}`}>
        <polyline points={pts} fill="none" className="spark-line" />
      </svg>
    </figure>
  );
}
''',
    'src/client/components/MissionScreen.tsx': r'''import { getScenario } from '../../engine/scenarios.ts';
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
''',
    'src/client/components/OutpostMap.tsx': r'''import type { SimulationState } from '../../engine/types.ts';
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
''',
    'src/client/components/Panels.tsx': r'''import * as K from '../../engine/constants.ts';
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
''',
    'src/client/components/SetupScreen.tsx': r'''import { useState } from 'react';
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
''',
    'src/client/hooks/useSimulation.ts': r'''import { useCallback, useEffect, useRef, useState } from 'react';
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
''',
    'src/client/persist.ts': r'''import type { Debrief } from '../engine/debrief.ts';
import type { SimulationState } from '../engine/types.ts';

const SAVE_KEY = 'ares-horizon:save';
const RUNS_KEY = 'ares-horizon:runs';

export interface RunSummary {
  scenarioId: string;
  seed: number;
  outcome: string;
  sols: number;
  score: number;
  survivors: number;
  at: string;
}

function safeGet(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}
function safeSet(key: string, value: string): void {
  try { localStorage.setItem(key, value); } catch { /* storage may be blocked: ignore */ }
}

export function saveGame(s: SimulationState): void { safeSet(SAVE_KEY, JSON.stringify(s)); }
export function loadGame(): SimulationState | null {
  const raw = safeGet(SAVE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw) as SimulationState; } catch { return null; }
}
export function clearGame(): void { try { localStorage.removeItem(SAVE_KEY); } catch { /* ignore */ } }

export function loadRuns(): RunSummary[] {
  const raw = safeGet(RUNS_KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) as RunSummary[]; } catch { return []; }
}
export function saveRun(s: SimulationState, d: Debrief): void {
  const runs = loadRuns();
  runs.unshift({ scenarioId: s.scenarioId, seed: s.seed, outcome: d.outcome, sols: d.sols, score: d.score, survivors: d.survivors, at: new Date().toISOString() });
  safeSet(RUNS_KEY, JSON.stringify(runs.slice(0, 20)));
}

/** Downloads the full run (state, cause log, history, debrief) as JSON for classroom debriefs. */
export function exportRun(s: SimulationState, d: Debrief): void {
  const blob = new Blob([JSON.stringify({ debrief: d, state: s }, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ares-horizon-${s.scenarioId}-seed${s.seed}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
''',
    'src/client/status.ts': r'''import type { Status, Telemetry } from '../engine/telemetry.ts';

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
''',
    'src/client/styles.css': r''':root {
  --bg: #020617;
  --surface: #0f172a;
  --card: #1e293b;
  --border: #334155;
  --text: #f8fafc;
  --text-2: #94a3b8;
  --text-3: #64748b;
  --nominal: #10b981;
  --warning: #f59e0b;
  --critical: #ef4444;
  --cyan: #06b6d4;
  --power: #facc15;
  --bio: #84cc16;
  --font-ui: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-display: 'Space Grotesk', 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  color-scheme: dark;
}

* { box-sizing: border-box; }
html, body, #root { min-height: 100%; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 16px/1.5 var(--font-ui);
}
h1, h2, h3 { font-family: var(--font-display); margin: 0; letter-spacing: -0.01em; }
h1 { font-size: 36px; line-height: 1.1; }
h2 { font-size: 18px; margin-bottom: 12px; }
h3 { font-size: 16px; margin-bottom: 4px; }
p { margin: 0 0 12px; }
ul, ol { margin: 0; padding-left: 20px; }
.mono { font-family: var(--font-mono); }
.muted { color: var(--text-2); }
.small { font-size: 13px; }
.lead { color: var(--text-2); font-size: 18px; max-width: 62ch; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

button {
  font: inherit; font-size: 14px; color: var(--text); background: var(--card);
  border: 1px solid var(--border); border-radius: 6px; padding: 8px 14px; cursor: pointer;
}
button:hover:not(:disabled) { border-color: var(--cyan); }
button:disabled { opacity: 0.45; cursor: not-allowed; }
button.primary { background: var(--cyan); border-color: var(--cyan); color: #00131a; font-weight: 600; }
button.ghost { background: transparent; }
button[aria-pressed='true'] { background: var(--cyan); border-color: var(--cyan); color: #00131a; }
:focus-visible { outline: 3px solid var(--power); outline-offset: 2px; }
input[type='number'] { background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; width: 120px; font-size: 14px; }
.button-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }

/* Setup and debrief */
.setup, .debrief { max-width: 860px; margin: 0 auto; padding: 48px 20px 64px; display: flex; flex-direction: column; gap: 24px; }
.scenario-list { border: 0; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.scenario-list legend { font-family: var(--font-display); font-size: 18px; margin-bottom: 8px; }
.scenario { display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; cursor: pointer; }
.scenario-on { border-color: var(--cyan); }
.scenario-blurb { display: block; color: var(--text-2); font-size: 14px; margin-top: 2px; }
.setup-row { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.howto p { color: var(--text-2); max-width: 70ch; }
.runs { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.chains { display: flex; flex-direction: column; gap: 20px; padding-left: 0; list-style: none; }
.chains > li { border-left: 3px solid var(--critical); padding-left: 16px; }
.chains ul { margin-bottom: 8px; }
.debrief section ul { max-width: 70ch; }

/* Mission */
.mission { min-height: 100vh; padding: 12px 16px 32px; }
.mission-alarm { box-shadow: inset 0 0 0 3px rgba(239, 68, 68, 0.55); animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 50% { box-shadow: inset 0 0 0 3px rgba(239, 68, 68, 0.15); } }
.topbar { display: grid; grid-template-columns: auto 1fr auto auto; gap: 16px; align-items: center; padding: 8px 0 12px; }
.topbar-title { font-size: 20px; }
.progress { height: 8px; background: var(--card); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--cyan); }
.speed { display: flex; gap: 4px; }
.alert-strip { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.chip { padding: 4px 10px; border-radius: 999px; font-size: 13px; border: 1px solid; }
.chip-warning { color: var(--warning); border-color: var(--warning); }
.chip-critical { color: var(--critical); border-color: var(--critical); }
.mission-grid { display: grid; grid-template-columns: minmax(300px, 5fr) 7fr; gap: 16px; align-items: start; }
.col { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.panel { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }

.gauge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
.gauge { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 10px; text-align: center; }
.gauge svg { width: 100%; max-width: 130px; }
.gauge-track { fill: none; stroke: var(--border); stroke-width: 8; stroke-linecap: round; }
.gauge-fill { fill: none; stroke: var(--nominal); stroke-width: 8; stroke-linecap: round; }
.gauge-warning .gauge-fill { stroke: var(--warning); }
.gauge-critical .gauge-fill { stroke: var(--critical); }
.gauge-critical { border-color: var(--critical); }
.gauge-value { font-size: 22px; margin-top: -22px; }
.gauge-unit { font-size: 12px; color: var(--text-2); }
.gauge-label { font-size: 13px; color: var(--text-2); }
.gauge-status { font-size: 13px; margin-top: 2px; }
.gauge-nominal .gauge-status { color: var(--nominal); }
.gauge-warning .gauge-status { color: var(--warning); }
.gauge-critical .gauge-status { color: var(--critical); }
.gauge-hint { font-size: 12px; color: var(--text-3); margin-top: 2px; }

.spark-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.spark { margin: 0; }
.spark figcaption { font-size: 13px; color: var(--text-2); display: flex; justify-content: space-between; gap: 8px; }
.spark svg { width: 100%; height: 56px; display: block; }
.spark-line { stroke: var(--cyan); stroke-width: 2; }
.spark-empty { height: 56px; color: var(--text-3); font-size: 13px; display: grid; place-items: center; }

.outpost-map { width: 100%; height: auto; }
.pipe { stroke-width: 3; stroke-dasharray: 5 5; opacity: 0.8; }
.pipe-power { stroke: var(--power); }
.pipe-air { stroke: var(--cyan); }
.pipe-bio { stroke: var(--bio); }
.pipe-heat { stroke: var(--warning); }
.mod rect { fill: var(--card); stroke: var(--nominal); stroke-width: 2; }
.mod-warning rect { stroke: var(--warning); }
.mod-critical rect { stroke: var(--critical); fill: #3b1219; }
.mod text { fill: var(--text); font: 600 10.5px var(--font-ui); }
.mod .mod-note { font-weight: 400; fill: var(--text-2); font-size: 10px; }
.mod .mod-status { font-weight: 600; font-size: 9.5px; fill: var(--nominal); }
.mod-warning .mod-status { fill: var(--warning); }
.mod-critical .mod-status { fill: var(--critical); }

.crew-list { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.crew-list li { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 10px; }
.crew-lost { opacity: 0.5; }
.bar-row { display: grid; grid-template-columns: 48px 1fr 28px; gap: 6px; align-items: center; margin-top: 4px; }
.bar { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; }
.bar-nominal { background: var(--nominal); }
.bar-warning { background: var(--warning); }
.bar-critical { background: var(--critical); }

.switch-list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.switch-row { display: flex; gap: 10px; align-items: flex-start; cursor: pointer; }
.switch-row input { margin-top: 5px; width: 18px; height: 18px; accent-color: var(--cyan); }
.switch-text { display: flex; flex-direction: column; }
.slider-row { display: flex; flex-direction: column; gap: 2px; margin-top: 14px; }
.slider-row input { width: 100%; accent-color: var(--cyan); }

.earth-list, .log-list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 6px; font-size: 14px; }
.earth-list li { border-left: 3px solid var(--cyan); padding-left: 10px; }
.log-list { margin-top: 12px; }
.log-crisis { color: var(--critical); }
.log-warning, .log-event { color: var(--warning); }
.log-recovery { color: var(--nominal); }
.log-action, .log-info { color: var(--text-2); }

@media (max-width: 900px) {
  .mission-grid { grid-template-columns: 1fr; }
  .topbar { grid-template-columns: 1fr auto; }
  .progress { grid-column: 1 / -1; order: 3; }
  h1 { font-size: 30px; }
}
@media (prefers-reduced-motion: reduce) {
  .mission-alarm { animation: none; }
  * { transition: none !important; }
}
''',
    'src/client/workers/sim.worker.ts': r'''/**
 * Runs the simulation off the main thread so the HUD stays smooth and the
 * clock keeps running when the tab is in the background.
 */
import { TICK_HZ } from '../../engine/constants.ts';
import { SimulationEngine } from '../../engine/SimulationEngine.ts';
import type { Action, SimulationState } from '../../engine/types.ts';

type InMsg =
  | { type: 'init'; scenarioId: string; seed: number; restore?: SimulationState }
  | { type: 'action'; action: Action }
  | { type: 'speed'; speed: number }
  | { type: 'stop' };

const ctx = self as unknown as {
  postMessage(m: unknown): void;
  onmessage: ((e: MessageEvent<InMsg>) => void) | null;
};

const TICK_MS = 1000 / TICK_HZ;
let engine: SimulationEngine | null = null;
let speed = 1;
let acc = 0;
let last = 0;
let timer: ReturnType<typeof setInterval> | null = null;

function post(): void {
  if (engine) ctx.postMessage({ type: 'state', state: engine.getState() });
}

function loop(): void {
  if (!engine) return;
  const now = performance.now();
  acc += (now - last) * speed;
  last = now;
  let n = Math.min(Math.floor(acc / TICK_MS), 200); // cap catch-up after a long stall
  acc = n > 0 ? acc - n * TICK_MS : acc;
  if (acc > 10 * TICK_MS) acc = 0;
  const wasActive = engine.peek().status === 'ACTIVE';
  while (n-- > 0 && engine.peek().status === 'ACTIVE') engine.step();
  if (speed > 0 && wasActive) post();
}

ctx.onmessage = (e) => {
  const m = e.data;
  if (m.type === 'init') {
    engine = new SimulationEngine(m.scenarioId, m.seed, m.restore);
    speed = 1;
    acc = 0;
    last = performance.now();
    if (timer) clearInterval(timer);
    timer = setInterval(loop, TICK_MS);
    post();
  } else if (m.type === 'action') {
    engine?.dispatch(m.action);
    post();
  } else if (m.type === 'speed') {
    speed = Math.max(0, m.speed);
    last = performance.now();
    post();
  } else if (m.type === 'stop') {
    if (timer) clearInterval(timer);
    timer = null;
    engine = null;
  }
};
''',
    'src/engine/SimulationEngine.ts': r'''/**
 * ARES HORIZON deterministic simulation engine.
 * Pure logic: no DOM, no timers. The UI (via a Web Worker) calls step() at 10 Hz.
 * Same scenario + same seed + same actions at the same ticks = same result.
 */
import * as K from './constants.ts';
import { diagnose } from './advice.ts';
import { nextFloat } from './rng.ts';
import { getScenario } from './scenarios.ts';
import { pCO2Kpa, pO2Kpa } from './telemetry.ts';
import type {
  Action,
  CauseKind,
  CrewMember,
  EventKind,
  ScenarioConfig,
  SimulationState,
} from './types.ts';

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
/** Whole sols elapsed. The epsilon absorbs floating-point error at exact sol boundaries. */
const solOf = (simTimeSec: number, solSeconds: number) => Math.floor(simTimeSec / solSeconds + 1e-9);

const CREW_TEMPLATE: Pick<CrewMember, 'name' | 'role'>[] = [
  { name: 'Okafor', role: 'Commander' },
  { name: 'Reyes', role: 'Engineer' },
  { name: 'Tanaka', role: 'Medic' },
  { name: 'Hussain', role: 'Botanist' },
];

export function createInitialState(scenarioId: string, seed: number): SimulationState {
  const sc = getScenario(scenarioId);
  const s: SimulationState = {
    scenarioId,
    seed,
    rngState: seed >>> 0,
    tick: 0,
    simTimeSec: 0,
    sol: 0,
    status: 'ACTIVE',
    env: { sunFactor: 0, ambientK: sc.ambientNightK, irradianceWm2: 0, doseRateMSvPerDay: 0, stormActive: false, speActive: false },
    power: {
      solarCapacityKw: sc.initial.solarCapacityKw,
      nuclearKw: sc.initial.nuclearKw,
      batteryKwh: sc.initial.batteryKwh,
      batteryMaxKwh: sc.initial.batteryMaxKwh,
      dustCoverage: 0,
      solarKw: 0,
      generationKw: 0,
      loadKw: 0,
      supplyRatio: 1,
    },
    eclss: {
      o2AtmKg: K.O2_ATM_NOMINAL_KG,
      o2TankKg: sc.initial.o2TankKg,
      o2TankMaxKg: sc.initial.o2TankMaxKg,
      co2Kg: 0.2,
      waterL: sc.initial.waterL,
      waterMaxL: sc.initial.waterMaxL,
      h2Kg: sc.initial.h2Kg,
    },
    thermal: {
      habTempK: K.NOMINAL_TEMP_K,
      targetK: K.NOMINAL_TEMP_K,
      radiatorM2: sc.initial.radiatorM2,
      radiatorBaseM2: sc.initial.radiatorM2,
      louverPct: sc.initial.louverPct,
      heaterKw: 0,
      heaterMaxKw: sc.initial.heaterMaxKw,
    },
    food: { kcal: sc.initial.kcal, cropHealth: sc.initial.cropHealth },
    shielding: { regolithCm: sc.initial.regolithCm },
    controls: { electrolysis: false, sabatier: false, scrubber: true, recycler: true, hydroponics: true, shelter: false },
    crew: [],
    events: [],
    flags: {},
    causeLog: [],
    history: [],
    nextHistorySimSec: 0,
    scheduledDone: [],
    earth: { pending: null, inbox: [] },
  };
  for (let i = 0; i < sc.crewCount; i++) {
    const t = CREW_TEMPLATE[i % CREW_TEMPLATE.length];
    s.crew.push({
      id: `crew-${i + 1}`,
      name: t.name,
      role: t.role,
      health: 100,
      stress: 10,
      doseMSv: 0,
      resilience: 0.9 + nextFloat(s) * 0.2,
      alive: true,
    });
  }
  return s;
}

export class SimulationEngine {
  private s: SimulationState;
  private sc: ScenarioConfig;

  constructor(scenarioId: string, seed = 1, restore?: SimulationState) {
    this.s = restore ? (structuredClone(restore) as SimulationState) : createInitialState(scenarioId, seed);
    this.sc = getScenario(this.s.scenarioId);
    if (!restore) this.log('INFO', 'MISSION_START', `${this.sc.title}: mission start. Crew of ${this.sc.crewCount} is healthy.`);
  }

  /** Simulated seconds covered by one tick. */
  get simSecondsPerTick(): number {
    return this.sc.solSeconds / (this.sc.secondsPerSolReal * K.TICK_HZ);
  }

  getState(): SimulationState {
    return structuredClone(this.s) as SimulationState;
  }

  /** Direct read access for tests and policies (do not mutate). */
  peek(): Readonly<SimulationState> {
    return this.s;
  }

  // ---------------------------------------------------------------- stepping
  step(): void {
    const s = this.s;
    if (s.status !== 'ACTIVE') return;
    const perTick = this.simSecondsPerTick;
    const dt = perTick / K.SUBSTEPS;

    this.processEvents(perTick);
    this.deliverAdvice();
    for (let i = 0; i < K.SUBSTEPS; i++) this.integrate(dt);
    s.tick += 1;
    s.sol = solOf(s.simTimeSec, this.sc.solSeconds);
    this.detectCrises();
    this.sampleHistory();
    this.checkEnd();
  }

  // ----------------------------------------------------------------- actions
  dispatch(a: Action): void {
    const s = this.s;
    if (s.status !== 'ACTIVE') return;
    switch (a.type) {
      case 'SET_SYSTEM': {
        if (s.controls[a.system] === a.on) return;
        s.controls[a.system] = a.on;
        this.log('ACTION', `SYSTEM_${a.system}_${a.on ? 'ON' : 'OFF'}`, `Operator turned ${a.system} ${a.on ? 'on' : 'off'}.`);
        return;
      }
      case 'SET_RADIATOR': {
        const v = clamp(Math.round(a.louverPct), 0, 100);
        if (v === s.thermal.louverPct) return;
        s.thermal.louverPct = v;
        this.log('ACTION', 'SET_RADIATOR', `Radiator louvers set to ${v}%.`);
        return;
      }
      case 'SET_HEATER': {
        const v = clamp(Math.round(a.maxKw), 0, 15);
        if (v === s.thermal.heaterMaxKw) return;
        s.thermal.heaterMaxKw = v;
        this.log('ACTION', 'SET_HEATER', `Heater limit set to ${v} kW.`);
        return;
      }
      case 'CLEAN_PANELS': {
        s.power.dustCoverage = Math.max(0, s.power.dustCoverage - 0.35);
        this.bumpStress(2);
        this.log('ACTION', 'CLEAN_PANELS', 'Crew cleaned the solar arrays.');
        return;
      }
      case 'ADD_SHIELDING': {
        if (s.shielding.regolithCm >= K.SHIELD_MAX_CM) return;
        s.shielding.regolithCm = Math.min(K.SHIELD_MAX_CM, s.shielding.regolithCm + K.SHIELD_STEP_CM);
        this.bumpStress(3);
        this.log('ACTION', 'ADD_SHIELDING', `Crew piled more regolith on the hab: ${s.shielding.regolithCm} cm.`);
        return;
      }
      case 'REPAIR_RADIATOR': {
        if (s.thermal.radiatorM2 >= s.thermal.radiatorBaseM2) return;
        s.thermal.radiatorM2 = s.thermal.radiatorBaseM2;
        this.bumpStress(3);
        this.log('ACTION', 'REPAIR_RADIATOR', 'Crew repaired the radiator.');
        return;
      }
      case 'REQUEST_EARTH_ADVICE': {
        if (s.earth.pending) return;
        s.earth.pending = { deliverAtTick: s.tick + 2 * this.sc.commDelayTicks, text: diagnose(s) };
        this.log('ACTION', 'REQUEST_ADVICE', 'Advice requested from Earth. The reply arrives after the signal delay.');
        return;
      }
    }
  }

  // --------------------------------------------------------------- internals
  private log(kind: CauseKind, code: string, message: string): void {
    const s = this.s;
    s.causeLog.push({ simTimeSec: s.simTimeSec, sol: solOf(s.simTimeSec, this.sc.solSeconds), kind, code, message });
    if (s.causeLog.length > 600) s.causeLog.shift();
  }

  private bumpStress(v: number): void {
    for (const c of this.s.crew) if (c.alive) c.stress = clamp(c.stress + v, 0, 100);
  }

  private hasEvent(kind: EventKind): boolean {
    return this.s.events.some((e) => e.kind === kind);
  }

  private startEvent(kind: EventKind): void {
    const s = this.s;
    const sol = this.sc.solSeconds;
    switch (kind) {
      case 'DUST_STORM': {
        const dur = (3 + nextFloat(s) * 2) * sol;
        s.events.push({ kind, startedAtSimSec: s.simTimeSec, endsAtSimSec: s.simTimeSec + dur });
        this.log('EVENT', 'DUST_STORM', 'Global dust storm: sunlight drops by about 88% and dust settles on the arrays.');
        return;
      }
      case 'SOLAR_PARTICLE_EVENT': {
        const dur = (0.5 + nextFloat(s) * 0.5) * sol;
        s.events.push({ kind, startedAtSimSec: s.simTimeSec, endsAtSimSec: s.simTimeSec + dur });
        this.log('EVENT', 'SOLAR_PARTICLE_EVENT', 'Solar particle event: radiation spike. Shelter the crew.');
        return;
      }
      case 'MICROMETEORITE': {
        s.thermal.radiatorM2 = Math.max(s.thermal.radiatorBaseM2 * 0.4, s.thermal.radiatorM2 * 0.75);
        this.log('EVENT', 'MICROMETEORITE', 'Micrometeorite puncture: radiator area reduced.');
        return;
      }
      case 'POWER_SURGE': {
        s.power.batteryKwh *= 0.7;
        this.log('EVENT', 'POWER_SURGE', 'Power surge blew a capacitor bank: 30% of battery charge lost.');
        return;
      }
    }
  }

  private processEvents(perTick: number): void {
    const s = this.s;
    const t = s.simTimeSec;
    this.sc.events.scheduled.forEach((ev, i) => {
      if (!s.scheduledDone.includes(i) && t >= ev.atSol * this.sc.solSeconds) {
        s.scheduledDone.push(i);
        if (!this.hasEvent(ev.kind)) this.startEvent(ev.kind);
      }
    });
    const f = perTick / this.sc.solSeconds;
    (Object.keys(this.sc.events.perSol) as EventKind[]).forEach((kind) => {
      const r = nextFloat(s); // always drawn, keeps the sequence stable
      const p = this.sc.events.perSol[kind] * f;
      if (p > 0 && r < p && !this.hasEvent(kind)) this.startEvent(kind);
    });
    s.events = s.events.filter((e) => {
      if (t < e.endsAtSimSec) return true;
      this.log('INFO', `${e.kind}_END`, e.kind === 'DUST_STORM' ? 'The dust storm has passed.' : 'The solar particle event has passed.');
      return false;
    });
  }

  private deliverAdvice(): void {
    const s = this.s;
    const p = s.earth.pending;
    if (p && s.tick >= p.deliverAtTick) {
      s.earth.inbox.push({ sol: solOf(s.simTimeSec, this.sc.solSeconds), text: p.text });
      s.earth.pending = null;
      this.log('INFO', 'ADVICE_RECEIVED', 'Earth replied. Check the message panel.');
    }
  }

  private sunFactor(t: number): number {
    const sc = this.sc;
    const p = ((t + sc.phaseOffsetSec) % sc.dayCycleSec) / sc.dayCycleSec;
    return p < sc.daylightFraction ? Math.sin((Math.PI * p) / sc.daylightFraction) : 0;
  }

  private integrate(dt: number): void {
    const s = this.s;
    const sc = this.sc;
    const c = s.controls;
    const f = dt / sc.solSeconds; // fraction of a sol
    const t = s.simTimeSec;

    // ---- environment
    const storm = this.hasEvent('DUST_STORM');
    const spe = this.hasEvent('SOLAR_PARTICLE_EVENT');
    const sun = this.sunFactor(t);
    s.env.sunFactor = sun;
    s.env.stormActive = storm;
    s.env.speActive = spe;
    s.env.ambientK = sc.ambientNightK + (sc.ambientDayK - sc.ambientNightK) * sun;
    s.env.irradianceWm2 = sc.solarIrradianceWm2 * sun * (storm ? 0.12 : 1);
    s.power.dustCoverage = clamp(
      s.power.dustCoverage + (storm ? sc.dustDepositionStormPerSol : sc.dustDepositionPerSol) * f,
      0,
      0.9,
    );

    // ---- power
    const solarKw = s.power.solarCapacityKw * (s.env.irradianceWm2 / 1000) * (1 - s.power.dustCoverage);
    const gen = solarKw + s.power.nuclearKw;
    const tHab = s.thermal.habTempK;
    const heaterKw =
      tHab < s.thermal.targetK ? s.thermal.heaterMaxKw * clamp((s.thermal.targetK - tHab) / 3, 0, 1) : 0;
    const nonHeater =
      K.LOAD_AVIONICS_KW +
      (c.scrubber ? K.LOAD_SCRUBBER_KW : 0) +
      (c.recycler ? K.LOAD_RECYCLER_KW : 0) +
      (c.electrolysis ? K.LOAD_ELECTROLYSIS_KW : 0) +
      (c.sabatier ? K.LOAD_SABATIER_KW : 0) +
      (c.hydroponics ? K.LOAD_HYDROPONICS_KW : 0);
    const load = nonHeater + heaterKw;
    let ratio = 1;
    const net = gen - load;
    if (net >= 0) {
      s.power.batteryKwh = Math.min(s.power.batteryMaxKwh, s.power.batteryKwh + (net * dt) / 3600);
    } else {
      const need = (-net * dt) / 3600;
      if (s.power.batteryKwh >= need) {
        s.power.batteryKwh -= need;
      } else {
        const availKw = (s.power.batteryKwh * 3600) / dt;
        ratio = clamp((gen + availKw) / load, 0, 1);
        s.power.batteryKwh = 0;
      }
    }
    s.power.solarKw = solarKw;
    s.power.generationKw = gen;
    s.power.loadKw = load;
    s.power.supplyRatio = ratio;
    s.thermal.heaterKw = heaterKw * ratio;

    // ---- thermal
    const heatW = (nonHeater * K.INTERNAL_HEAT_FRACTION + heaterKw) * 1000 * ratio;
    const aEff = s.thermal.radiatorM2 * (s.thermal.louverPct / 100);
    const tEnv = s.env.ambientK;
    const radW = K.EMISSIVITY * K.STEFAN_BOLTZMANN * aEff * (tHab ** 4 - tEnv ** 4);
    const hullW = K.HULL_W_PER_K * (tHab - tEnv);
    s.thermal.habTempK = clamp(tHab + ((heatW - radW - hullW) * dt) / K.HAB_HEAT_CAPACITY_J_PER_K, 150, 350);

    // ---- life support
    const e = s.eclss;
    const alive = s.crew.filter((m) => m.alive).length;
    e.o2AtmKg = Math.max(0, e.o2AtmKg - alive * K.O2_KG_PER_CREW_SOL * f);
    if (e.o2AtmKg < K.O2_ATM_NOMINAL_KG) {
      const move = Math.min(K.O2_ATM_NOMINAL_KG - e.o2AtmKg, e.o2TankKg);
      e.o2AtmKg += move;
      e.o2TankKg -= move;
    }
    e.co2Kg += alive * K.CO2_KG_PER_CREW_SOL * f;
    const recycled = c.recycler ? K.RECYCLER_EFFICIENCY * ratio : 0;
    e.waterL = Math.max(0, e.waterL - alive * K.WATER_L_PER_CREW_SOL * f * (1 - recycled));
    s.food.kcal = Math.max(0, s.food.kcal - alive * K.KCAL_PER_CREW_SOL * f);

    if (c.electrolysis && e.waterL > 1 && e.o2TankKg < e.o2TankMaxKg && e.h2Kg < K.H2_STORE_MAX_KG) {
      const w = Math.min(K.ELECTROLYSIS_WATER_KG_PER_SOL * ratio * f, e.waterL);
      e.waterL -= w;
      e.o2TankKg = Math.min(e.o2TankMaxKg, e.o2TankKg + w * K.ELECTROLYSIS_O2_PER_KG_WATER);
      e.h2Kg = Math.min(K.H2_STORE_MAX_KG, e.h2Kg + w * K.ELECTROLYSIS_H2_PER_KG_WATER);
    }
    if (c.sabatier) {
      const p = Math.min(K.SABATIER_CO2_KG_PER_SOL * ratio * f, e.co2Kg, e.h2Kg / K.SABATIER_H2_PER_KG_CO2);
      if (p > 0) {
        e.co2Kg -= p;
        e.h2Kg -= p * K.SABATIER_H2_PER_KG_CO2;
        e.waterL = Math.min(e.waterMaxL, e.waterL + p * K.SABATIER_WATER_PER_KG_CO2);
      }
    }
    if (c.scrubber) e.co2Kg -= Math.min(e.co2Kg, K.SCRUBBER_CO2_KG_PER_SOL * ratio * f);

    // ---- hydroponics
    const tOk = s.thermal.habTempK >= 288 && s.thermal.habTempK <= 303;
    if (c.hydroponics && ratio > 0.5 && e.waterL > 5 && tOk) {
      const crop = s.food.cropHealth;
      s.food.cropHealth = Math.min(1, crop + 0.35 * f);
      e.waterL = Math.max(0, e.waterL - K.HYDRO_WATER_L_PER_SOL * f);
      s.food.kcal += K.HYDRO_KCAL_PER_SOL * crop * f;
      e.o2TankKg = Math.min(e.o2TankMaxKg, e.o2TankKg + K.HYDRO_O2_KG_PER_SOL * crop * f);
      e.co2Kg = Math.max(0, e.co2Kg - K.HYDRO_CO2_KG_PER_SOL * crop * f);
    } else {
      s.food.cropHealth = Math.max(0, s.food.cropHealth - 0.15 * f);
    }

    // ---- radiation
    const shield = Math.exp(-K.SHIELD_MU_PER_CM * s.shielding.regolithCm);
    const rate =
      sc.radiationMSvPerDay * (spe ? K.SPE_DOSE_MULTIPLIER : 1) * shield * (c.shelter ? K.SHELTER_DOSE_FACTOR : 1);
    s.env.doseRateMSvPerDay = rate;

    // ---- crew
    const po2 = pO2Kpa(s);
    const pco2 = pCO2Kpa(s);
    const tNow = s.thermal.habTempK;
    for (const m of s.crew) {
      if (!m.alive) continue;
      let dmg = 0;
      let hazards = 0;
      if (po2 < K.T.severeHypoxiaKpa) { dmg += 150; hazards++; }
      else if (po2 < K.T.hypoxiaKpa) { dmg += 40; hazards++; }
      if (pco2 > K.T.co2SevereKpa) { dmg += 80; hazards++; }
      else if (pco2 > K.T.co2HighKpa) { dmg += 20; hazards++; }
      if (tNow < K.T.severeColdK || tNow > K.T.severeHotK) { dmg += 60; hazards++; }
      else if (tNow < K.T.coldK || tNow > K.T.hotK) { dmg += 15; hazards++; }
      if (e.waterL <= 0.5) { dmg += 60; hazards++; }
      if (s.food.kcal <= 0) { dmg += 8; hazards++; }
      if (rate > K.T.doseRateHighMSvPerDay) { dmg += (rate - K.T.doseRateHighMSvPerDay) * 0.8; hazards++; }
      if (m.stress > 80) dmg += 5;
      const roleFactor = m.role === 'Medic' ? 0.85 : 1;
      dmg = (dmg * roleFactor) / m.resilience;
      m.doseMSv += rate * f;
      if (dmg > 0) m.health -= dmg * f;
      else if (m.stress < 50) m.health = Math.min(100, m.health + 3 * f);
      let dStress = hazards > 0 ? 20 * hazards : s.events.length > 0 ? 3 : -6;
      dStress += 1 + (c.shelter ? 6 : 0);
      if (m.role === 'Commander') dStress *= dStress > 0 ? 0.8 : 1;
      m.stress = clamp(m.stress + dStress * f, 0, 100);
      if (m.health <= 0) {
        m.health = 0;
        m.alive = false;
        this.log('CRISIS', `CREW_LOST_${m.id}`, `${m.name} (${m.role}) did not survive.`);
      }
    }
    s.simTimeSec += dt;
  }

  private detectCrises(): void {
    const s = this.s;
    const po2 = pO2Kpa(s);
    const pco2 = pCO2Kpa(s);
    const checks: [string, boolean, CauseKind, string, string][] = [
      ['BATTERY_EMPTY', s.power.supplyRatio < 0.99, 'CRISIS', 'Battery empty and supply below demand: systems are browning out.', 'Power supply is back to normal.'],
      ['LOW_O2', po2 < K.T.hypoxiaKpa, 'CRISIS', 'Oxygen pressure is below the safe limit.', 'Oxygen pressure is back in range.'],
      ['HIGH_CO2', pco2 > K.T.co2HighKpa, 'CRISIS', 'Carbon dioxide pressure is above the safe limit.', 'Carbon dioxide is back in range.'],
      ['COLD', s.thermal.habTempK < K.T.coldK, 'CRISIS', 'Cabin temperature fell below the safe limit.', 'Cabin temperature is back in range.'],
      ['HOT', s.thermal.habTempK > K.T.hotK, 'CRISIS', 'Cabin temperature rose above the safe limit.', 'Cabin temperature is back in range.'],
      ['NO_WATER', s.eclss.waterL <= 0.5, 'CRISIS', 'Drinking water ran out.', 'Water supply recovered.'],
      ['NO_FOOD', s.food.kcal <= 0, 'CRISIS', 'The food pantry is empty.', 'Food supply recovered.'],
      ['HIGH_RADIATION', s.env.doseRateMSvPerDay > K.T.doseRateHighMSvPerDay, 'CRISIS', 'Crew radiation dose rate is dangerously high.', 'Radiation dose rate is back to normal.'],
      ['O2_RESERVE_LOW', s.eclss.o2TankKg / s.eclss.o2TankMaxKg < K.T.lowTankFraction, 'WARNING', 'Oxygen reserve tank is below 20%.', 'Oxygen reserve is above 20% again.'],
    ];
    for (const [code, active, kind, msg, okMsg] of checks) {
      const was = !!s.flags[code];
      if (active && !was) {
        s.flags[code] = true;
        this.log(kind, code, msg);
      } else if (!active && was) {
        s.flags[code] = false;
        this.log('RECOVERY', `${code}_OK`, okMsg);
      }
    }
  }

  private sampleHistory(): void {
    const s = this.s;
    if (s.simTimeSec < s.nextHistorySimSec) return;
    s.nextHistorySimSec = s.simTimeSec + this.sc.solSeconds / 8;
    const n = Math.max(1, s.crew.length);
    const alive = s.crew.filter((m) => m.alive);
    s.history.push({
      sol: s.simTimeSec / this.sc.solSeconds,
      batteryKwh: s.power.batteryKwh,
      netKw: s.power.generationKw - s.power.loadKw,
      pO2Kpa: pO2Kpa(s),
      pCO2Kpa: pCO2Kpa(s),
      habTempK: s.thermal.habTempK,
      waterL: s.eclss.waterL,
      kcal: s.food.kcal,
      avgHealth: s.crew.reduce((a, m) => a + m.health, 0) / n,
      avgStress: alive.length ? alive.reduce((a, m) => a + m.stress, 0) / alive.length : 100,
    });
  }

  private checkEnd(): void {
    const s = this.s;
    if (!s.crew.some((m) => m.alive)) {
      s.status = 'FAILED';
      this.log('CRISIS', 'MISSION_FAILED', 'All crew lost. Mission failed.');
    } else if (s.simTimeSec >= this.sc.targetSols * this.sc.solSeconds) {
      s.status = 'SUCCESS';
      this.log('INFO', 'MISSION_SUCCESS', `Sol ${this.sc.targetSols} reached with survivors. Mission complete.`);
    }
  }
}
''',
    'src/engine/advice.ts': r'''import { T } from './constants.ts';
import { pCO2Kpa, pO2Kpa } from './telemetry.ts';
import type { SimulationState } from './types.ts';

/** Mission Control's diagnosis. Rule-based so it is deterministic and testable. */
export function diagnose(s: SimulationState): string {
  const battPct = (100 * s.power.batteryKwh) / s.power.batteryMaxKwh;
  const tankPct = s.eclss.o2TankKg / s.eclss.o2TankMaxKg;
  if (s.env.speActive && !s.controls.shelter)
    return 'Solar particle event in progress. Move the crew into the shelter now and add regolith shielding when it passes.';
  if (!s.controls.scrubber || pCO2Kpa(s) > T.co2HighKpa)
    return 'CO2 is the fastest killer. Keep the scrubber running and let the Sabatier reactor recover water when hydrogen allows.';
  if (battPct < 20)
    return 'Battery is low. Shed non-essential loads first: hydroponics, then Sabatier, then electrolysis.';
  if (s.thermal.habTempK < T.coldK + 4)
    return 'Cabin is getting cold. Close the radiator louvers and raise the heater limit, then watch battery drain.';
  if (s.thermal.habTempK > T.hotK - 4)
    return 'Cabin is getting hot. Open the radiator louvers and switch off heavy loads.';
  if (s.thermal.radiatorM2 < s.thermal.radiatorBaseM2 - 0.1)
    return 'Radiator area is reduced after the puncture. Send a repair crew when the cabin is stable.';
  if (s.power.dustCoverage > 0.4)
    return 'Dust on the solar arrays is costing you power. Clean the panels once the storm eases.';
  if (tankPct < 0.4 && !s.controls.electrolysis)
    return 'Oxygen reserve is falling. Run electrolysis while you have spare power and water.';
  if (s.eclss.waterL < 0.25 * s.eclss.waterMaxL)
    return 'Water is low. Keep the recycler on and run the Sabatier reactor to recover water from CO2.';
  if (pO2Kpa(s) < T.hypoxiaKpa + 2)
    return 'Oxygen pressure is dropping. Check the reserve tank and electrolysis.';
  return 'All systems look nominal from here. Keep an eye on power and the next weather forecast.';
}
''',
    'src/engine/constants.ts': r'''/**
 * Physical constants and gameplay-scaled rates.
 * Every value marked ASSUMPTION must be verified and cited in docs/SOURCES.md
 * (task T09). Rates are per "sol" (one local solar day) unless noted.
 */
export const STEFAN_BOLTZMANN = 5.670374e-8; // W/(m^2 K^4)
export const R_GAS = 8.314462618; // J/(mol K)
export const MOLAR_O2 = 0.031998; // kg/mol
export const MOLAR_CO2 = 0.04401; // kg/mol

export const TICK_HZ = 10; // engine ticks per real second at 1x speed
export const SUBSTEPS = 4; // sub-steps per tick keep explicit Euler stable
export const HAB_VOLUME_M3 = 200; // ASSUMPTION: pressurised volume
export const HAB_HEAT_CAPACITY_J_PER_K = 6.0e6; // ASSUMPTION: gameplay-scaled
export const HULL_W_PER_K = 20; // ASSUMPTION: conductive hull loss
export const EMISSIVITY = 0.92;
export const NOMINAL_TEMP_K = 294;
export const O2_NOMINAL_PP_KPA = 21.3;

/** Mass of O2 that gives the nominal partial pressure at 294 K in the hab. */
export const O2_ATM_NOMINAL_KG =
  (O2_NOMINAL_PP_KPA * 1000 * HAB_VOLUME_M3 * MOLAR_O2) / (R_GAS * NOMINAL_TEMP_K);

// Crew needs per crew member per sol. ASSUMPTION: verify against NASA BVAD.
export const O2_KG_PER_CREW_SOL = 0.84;
export const CO2_KG_PER_CREW_SOL = 1.0;
export const WATER_L_PER_CREW_SOL = 2.5;
export const KCAL_PER_CREW_SOL = 2500;

// Stoichiometry (kg of product or reactant per kg of reference species).
// 2 H2O -> 2 H2 + O2 : per kg water
export const ELECTROLYSIS_O2_PER_KG_WATER = 31.998 / 36.03;
export const ELECTROLYSIS_H2_PER_KG_WATER = 4.032 / 36.03;
// CO2 + 4 H2 -> CH4 + 2 H2O : per kg CO2
export const SABATIER_WATER_PER_KG_CO2 = 36.03 / 44.01;
export const SABATIER_H2_PER_KG_CO2 = 8.064 / 44.01;

// Device rates (per sol) and electrical loads (kW). ASSUMPTION: gameplay values.
export const ELECTROLYSIS_WATER_KG_PER_SOL = 5.0;
export const SABATIER_CO2_KG_PER_SOL = 10.0;
export const SCRUBBER_CO2_KG_PER_SOL = 5.2;
export const RECYCLER_EFFICIENCY = 0.85;
export const H2_STORE_MAX_KG = 3.0;
export const HYDRO_WATER_L_PER_SOL = 6;
export const HYDRO_KCAL_PER_SOL = 9000;
export const HYDRO_O2_KG_PER_SOL = 1.0;
export const HYDRO_CO2_KG_PER_SOL = 1.2;

export const LOAD_AVIONICS_KW = 2.0;
export const LOAD_SCRUBBER_KW = 1.5;
export const LOAD_RECYCLER_KW = 1.0;
export const LOAD_ELECTROLYSIS_KW = 6.0;
export const LOAD_SABATIER_KW = 3.5;
export const LOAD_HYDROPONICS_KW = 4.0;
export const INTERNAL_HEAT_FRACTION = 0.85;

// Radiation. ASSUMPTION: mass attenuation is simplified to I = I0 exp(-mu x).
export const SHIELD_MU_PER_CM = 0.015;
export const SPE_DOSE_MULTIPLIER = 100;
export const SHELTER_DOSE_FACTOR = 0.25;
export const SHIELD_STEP_CM = 10;
export const SHIELD_MAX_CM = 100;

// Thresholds used by crew damage and crisis detection.
export const T = {
  hypoxiaKpa: 16,
  severeHypoxiaKpa: 12,
  co2HighKpa: 0.5,
  co2SevereKpa: 1.0,
  coldK: 283,
  hotK: 305,
  severeColdK: 273,
  severeHotK: 315,
  doseRateHighMSvPerDay: 30,
  lowTankFraction: 0.2,
} as const;
''',
    'src/engine/debrief.ts': r'''import { getScenario } from './scenarios.ts';
import type { CauseEntry, SimulationState } from './types.ts';

export interface CrisisChain {
  crisis: CauseEntry;
  causes: CauseEntry[];
  explanation: string;
}

export interface Debrief {
  outcome: 'SUCCESS' | 'FAILED' | 'ACTIVE';
  sols: number;
  score: number;
  survivors: number;
  crewSize: number;
  avgHealth: number;
  avgStress: number;
  peakDoseMSv: number;
  chains: CrisisChain[];
  lessons: string[];
}

/** Teaching text per crisis code: the "why" a student should take away. */
const EXPLANATIONS: Record<string, { why: string; lesson: string }> = {
  BATTERY_EMPTY: {
    why: 'Generation fell below demand and the battery ran dry, so every powered system slowed down at once.',
    lesson: 'Power is the root of the system: when it fails, life support, heating and crops all fail together. Shed non-essential loads before the battery is empty.',
  },
  LOW_O2: {
    why: 'Oxygen is consumed by the crew every sol. When the reserve tank empties, the cabin pressure of oxygen falls.',
    lesson: 'Electrolysis turns water and electricity into oxygen, so oxygen depends on both water and power.',
  },
  HIGH_CO2: {
    why: 'Crew breathe out carbon dioxide continuously. Without the scrubber (or Sabatier reactor) it builds up in the cabin.',
    lesson: 'Carbon dioxide builds up fast and is dangerous at low levels. The scrubber needs power, so a power shortage becomes an air problem.',
  },
  COLD: {
    why: 'The cabin loses heat to space through the hull and radiators. Low power meant less equipment heat and a weaker heater.',
    lesson: 'Thermal control is a balance: close the radiator louvers to keep heat in, but the heater draws battery power.',
  },
  HOT: {
    why: 'Equipment heat built up faster than the radiators could remove it.',
    lesson: 'Heat has to go somewhere. Open the radiator louvers or switch off heavy loads.',
  },
  NO_WATER: {
    why: 'Water is used for drinking, crops and electrolysis, and only partly recovered.',
    lesson: 'Water is a closed loop. The recycler and the Sabatier reactor recover it, and both need power.',
  },
  NO_FOOD: {
    why: 'The pantry ran out because hydroponics produced too little (it needs power, water and a warm cabin).',
    lesson: 'Growing food competes with other systems for power and water. Decide early how much to rely on crops.',
  },
  HIGH_RADIATION: {
    why: 'A solar particle event sent a burst of radiation through the shielding.',
    lesson: 'Shielding thickness reduces dose exponentially, and sheltering cuts it further. Build shielding before the storm, not during it.',
  },
};

export function computeScore(s: SimulationState): number {
  const n = Math.max(1, s.crew.length);
  const alive = s.crew.filter((c) => c.alive);
  const avgHealth = s.crew.reduce((a, c) => a + c.health, 0) / n;
  const avgStress = alive.length ? alive.reduce((a, c) => a + c.stress, 0) / alive.length : 100;
  const raw = 0.5 * (alive.length / n) + 0.3 * (avgHealth / 100) + 0.2 * (1 - avgStress / 100);
  return Math.round(100 * Math.max(0, Math.min(1, raw)));
}

export function buildDebrief(s: SimulationState): Debrief {
  const sc = getScenario(s.scenarioId);
  const lookback = 1.5 * sc.solSeconds;
  const crises = s.causeLog.filter((e) => e.kind === 'CRISIS' && EXPLANATIONS[e.code]);
  const chains: CrisisChain[] = crises.map((crisis) => {
    const causes = s.causeLog.filter(
      (e) =>
        e.simTimeSec <= crisis.simTimeSec &&
        e.simTimeSec >= crisis.simTimeSec - lookback &&
        e !== crisis &&
        (e.kind === 'EVENT' || e.kind === 'ACTION' || e.kind === 'WARNING' || (e.kind === 'CRISIS' && e.code !== crisis.code)),
    );
    return { crisis, causes: causes.slice(-5), explanation: EXPLANATIONS[crisis.code].why };
  });
  const codes = Array.from(new Set(crises.map((c) => c.code)));
  const lessons = codes.map((c) => EXPLANATIONS[c].lesson);
  const alive = s.crew.filter((c) => c.alive);
  const n = Math.max(1, s.crew.length);
  return {
    outcome: s.status,
    sols: s.sol,
    score: computeScore(s),
    survivors: alive.length,
    crewSize: s.crew.length,
    avgHealth: s.crew.reduce((a, c) => a + c.health, 0) / n,
    avgStress: alive.length ? alive.reduce((a, c) => a + c.stress, 0) / alive.length : 100,
    peakDoseMSv: Math.max(0, ...s.crew.map((c) => c.doseMSv)),
    chains,
    lessons: lessons.length ? lessons : ['No crises this run. Try the harder scenario or a new seed.'],
  };
}
''',
    'src/engine/policies.ts': r'''import { pCO2Kpa } from './telemetry.ts';
import type { Action, SimulationState } from './types.ts';

/** A policy looks at the state and returns actions. Used by tests and the balance check. */
export type Policy = (s: Readonly<SimulationState>) => Action[];

/** Does nothing: the starting configuration runs unattended. */
export const idlePolicy: Policy = () => [];

/** Switches every life-support system off. Must always fail. */
export const sabotagePolicy: Policy = (s) =>
  (['scrubber', 'recycler', 'hydroponics'] as const)
    .filter((k) => s.controls[k])
    .map((k): Action => ({ type: 'SET_SYSTEM', system: k, on: false }));

/** A reasonable operator. Shows the game is winnable and teaches the intended trade-offs. */
export const competentPolicy: Policy = (s) => {
  const a: Action[] = [];
  const set = (system: 'electrolysis' | 'sabatier' | 'scrubber' | 'recycler' | 'hydroponics' | 'shelter', on: boolean) => {
    if (s.controls[system] !== on) a.push({ type: 'SET_SYSTEM', system, on });
  };
  const battPct = (100 * s.power.batteryKwh) / s.power.batteryMaxKwh;
  const tankPct = (100 * s.eclss.o2TankKg) / s.eclss.o2TankMaxKg;

  set('scrubber', true);
  set('recycler', true);
  set('shelter', s.env.speActive);

  // Shed loads when the battery is low, restore when it recovers.
  if (battPct < 35) {
    set('hydroponics', false);
    set('sabatier', false);
    set('electrolysis', false);
  } else if (battPct > 60) {
    set('hydroponics', true);
    set('electrolysis', tankPct < 90 && s.eclss.waterL > 60);
    set('sabatier', pCO2Kpa(s) > 0.05 && s.eclss.h2Kg > 0.1);
  }

  // Thermal control with the louvers.
  const T = s.thermal.habTempK;
  if (T < 291 && s.thermal.louverPct > 0) a.push({ type: 'SET_RADIATOR', louverPct: Math.max(0, s.thermal.louverPct - 5) });
  if (T > 297 && s.thermal.louverPct < 100) a.push({ type: 'SET_RADIATOR', louverPct: Math.min(100, s.thermal.louverPct + 5) });

  if (s.power.dustCoverage > 0.3 && !s.env.stormActive) a.push({ type: 'CLEAN_PANELS' });
  if (s.thermal.radiatorM2 < s.thermal.radiatorBaseM2 && !s.env.speActive) a.push({ type: 'REPAIR_RADIATOR' });
  if (s.shielding.regolithCm < 40 && !s.env.speActive && s.tick % 50 === 0) a.push({ type: 'ADD_SHIELDING' });
  return a;
};
''',
    'src/engine/rng.ts': r'''/** Seeded PRNG (mulberry32). State lives in the simulation state so runs can be saved and replayed. */
export function nextFloat(holder: { rngState: number }): number {
  holder.rngState = (holder.rngState + 0x6d2b79f5) >>> 0;
  let t = holder.rngState;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}
''',
    'src/engine/scenarios.ts': r'''import type { ScenarioConfig } from './types.ts';

/**
 * Scenario data. Numbers marked ASSUMPTION are gameplay-scaled and must be
 * checked against NASA sources and recorded in docs/SOURCES.md (task T09).
 * To add a scenario: add an object here and the UI picks it up automatically.
 */
export const SCENARIOS: ScenarioConfig[] = [
  {
    id: 'mars-dust-storm',
    title: 'The Martian Dust Winter',
    body: 'Mars',
    blurb: 'A global dust storm cuts sunlight by about 88%. Keep four astronauts alive until Sol 15.',
    solSeconds: 88775, // Mars solar day, about 24 h 39 m 35 s
    secondsPerSolReal: 60,
    targetSols: 15,
    dayCycleSec: 88775,
    daylightFraction: 0.5,
    phaseOffsetSec: 0,
    solarIrradianceWm2: 590, // ASSUMPTION: mean top-of-atmosphere value, verify
    ambientDayK: 240, // ASSUMPTION
    ambientNightK: 190, // ASSUMPTION
    radiationMSvPerDay: 0.67, // ASSUMPTION: roughly the measured Mars surface dose, verify
    dustDepositionPerSol: 0.005,
    dustDepositionStormPerSol: 0.06,
    commDelayTicks: 200, // gameplay-scaled; real one-way delay is minutes
    crewCount: 4,
    initial: {
      solarCapacityKw: 30,
      nuclearKw: 10,
      batteryKwh: 150,
      batteryMaxKwh: 150,
      o2TankKg: 25,
      o2TankMaxKg: 60,
      waterL: 300,
      waterMaxL: 500,
      kcal: 80000,
      radiatorM2: 40,
      louverPct: 40,
      heaterMaxKw: 10,
      regolithCm: 20,
      h2Kg: 0.5,
      cropHealth: 0.8,
    },
    events: {
      perSol: { DUST_STORM: 0, SOLAR_PARTICLE_EVENT: 0.08, MICROMETEORITE: 0.06, POWER_SURGE: 0.04 },
      scheduled: [{ atSol: 2, kind: 'DUST_STORM' }],
    },
  },
  {
    id: 'moon-lunar-night',
    title: 'Lunar Night at the South Pole Ridge',
    body: 'Moon',
    blurb: 'The Sun sets about five days in and stays down for the rest of the mission. Nuclear power and batteries carry you.',
    solSeconds: 86400,
    secondsPerSolReal: 60,
    targetSols: 15,
    dayCycleSec: 2551392, // 29.53 Earth days
    daylightFraction: 0.5, // about 354 hours of night
    phaseOffsetSec: 864000, // start 10 days into the lunar day
    solarIrradianceWm2: 1361,
    ambientDayK: 220, // ASSUMPTION: polar ridge, simplified
    ambientNightK: 100, // ASSUMPTION
    radiationMSvPerDay: 1.37, // ASSUMPTION: roughly the measured lunar surface dose, verify
    dustDepositionPerSol: 0.008,
    dustDepositionStormPerSol: 0.008,
    commDelayTicks: 20, // real one-way delay is about 1.3 s
    crewCount: 4,
    initial: {
      solarCapacityKw: 20,
      nuclearKw: 10,
      batteryKwh: 150,
      batteryMaxKwh: 150,
      o2TankKg: 25,
      o2TankMaxKg: 60,
      waterL: 300,
      waterMaxL: 500,
      kcal: 80000,
      radiatorM2: 40,
      louverPct: 40,
      heaterMaxKw: 10,
      regolithCm: 20,
      h2Kg: 0.5,
      cropHealth: 0.8,
    },
    events: {
      perSol: { DUST_STORM: 0, SOLAR_PARTICLE_EVENT: 0.1, MICROMETEORITE: 0.1, POWER_SURGE: 0.04 },
      scheduled: [{ atSol: 3, kind: 'SOLAR_PARTICLE_EVENT' }],
    },
  },
];

export function getScenario(id: string): ScenarioConfig {
  const s = SCENARIOS.find((x) => x.id === id);
  if (!s) throw new Error(`Unknown scenario: ${id}`);
  return s;
}
''',
    'src/engine/telemetry.ts': r'''import { HAB_VOLUME_M3, MOLAR_CO2, MOLAR_O2, R_GAS } from './constants.ts';
import type { SimulationState } from './types.ts';

export type Status = 'nominal' | 'warning' | 'critical';

export function pO2Kpa(s: SimulationState): number {
  return ((s.eclss.o2AtmKg / MOLAR_O2) * R_GAS * s.thermal.habTempK) / HAB_VOLUME_M3 / 1000;
}
export function pCO2Kpa(s: SimulationState): number {
  return ((s.eclss.co2Kg / MOLAR_CO2) * R_GAS * s.thermal.habTempK) / HAB_VOLUME_M3 / 1000;
}

export interface Telemetry {
  pO2Kpa: number;
  pCO2Kpa: number;
  netKw: number;
  batteryPct: number;
  o2TankPct: number;
  waterPct: number;
  foodDays: number;
  habTempK: number;
  avgHealth: number;
  avgStress: number;
  alive: number;
}

export function getTelemetry(s: SimulationState): Telemetry {
  const alive = s.crew.filter((c) => c.alive);
  const n = Math.max(1, s.crew.length);
  return {
    pO2Kpa: pO2Kpa(s),
    pCO2Kpa: pCO2Kpa(s),
    netKw: s.power.generationKw - s.power.loadKw,
    batteryPct: (100 * s.power.batteryKwh) / s.power.batteryMaxKwh,
    o2TankPct: (100 * s.eclss.o2TankKg) / s.eclss.o2TankMaxKg,
    waterPct: (100 * s.eclss.waterL) / s.eclss.waterMaxL,
    foodDays: alive.length ? s.food.kcal / (alive.length * 2500) : 0,
    habTempK: s.thermal.habTempK,
    avgHealth: s.crew.reduce((a, c) => a + c.health, 0) / n,
    avgStress: alive.length ? alive.reduce((a, c) => a + c.stress, 0) / alive.length : 100,
    alive: alive.length,
  };
}
''',
    'src/engine/types.ts': r'''export type EventKind = 'DUST_STORM' | 'SOLAR_PARTICLE_EVENT' | 'MICROMETEORITE' | 'POWER_SURGE';
export type SystemName = 'electrolysis' | 'sabatier' | 'scrubber' | 'recycler' | 'hydroponics' | 'shelter';
export type MissionStatus = 'ACTIVE' | 'SUCCESS' | 'FAILED';

export interface ScenarioConfig {
  id: string;
  title: string;
  body: 'Mars' | 'Moon';
  blurb: string;
  solSeconds: number; // length of one local day in simulated seconds
  secondsPerSolReal: number; // real seconds per sol at 1x speed
  targetSols: number;
  dayCycleSec: number; // length of the light/dark cycle
  daylightFraction: number;
  phaseOffsetSec: number; // where in the cycle the mission starts
  solarIrradianceWm2: number;
  ambientDayK: number;
  ambientNightK: number;
  radiationMSvPerDay: number;
  dustDepositionPerSol: number;
  dustDepositionStormPerSol: number;
  commDelayTicks: number; // gameplay-scaled one-way delay, see docs/SOURCES.md
  crewCount: number;
  initial: {
    solarCapacityKw: number;
    nuclearKw: number;
    batteryKwh: number;
    batteryMaxKwh: number;
    o2TankKg: number;
    o2TankMaxKg: number;
    waterL: number;
    waterMaxL: number;
    kcal: number;
    radiatorM2: number;
    louverPct: number;
    heaterMaxKw: number;
    regolithCm: number;
    h2Kg: number;
    cropHealth: number;
  };
  events: {
    perSol: Record<EventKind, number>;
    scheduled: { atSol: number; kind: EventKind }[];
  };
}

export interface CrewMember {
  id: string;
  name: string;
  role: 'Commander' | 'Engineer' | 'Medic' | 'Botanist';
  health: number;
  stress: number;
  doseMSv: number;
  resilience: number;
  alive: boolean;
}

export interface ActiveEvent {
  kind: EventKind;
  startedAtSimSec: number;
  endsAtSimSec: number;
}

export type CauseKind = 'EVENT' | 'ACTION' | 'CRISIS' | 'WARNING' | 'RECOVERY' | 'INFO';
export interface CauseEntry {
  simTimeSec: number;
  sol: number;
  kind: CauseKind;
  code: string;
  message: string;
}

export interface HistoryPoint {
  sol: number;
  batteryKwh: number;
  netKw: number;
  pO2Kpa: number;
  pCO2Kpa: number;
  habTempK: number;
  waterL: number;
  kcal: number;
  avgHealth: number;
  avgStress: number;
}

export interface EarthMessage {
  sol: number;
  text: string;
}

export interface Controls {
  electrolysis: boolean;
  sabatier: boolean;
  scrubber: boolean;
  recycler: boolean;
  hydroponics: boolean;
  shelter: boolean;
}

export interface SimulationState {
  scenarioId: string;
  seed: number;
  rngState: number;
  tick: number;
  simTimeSec: number;
  sol: number;
  status: MissionStatus;
  env: {
    sunFactor: number;
    ambientK: number;
    irradianceWm2: number;
    doseRateMSvPerDay: number;
    stormActive: boolean;
    speActive: boolean;
  };
  power: {
    solarCapacityKw: number;
    nuclearKw: number;
    batteryKwh: number;
    batteryMaxKwh: number;
    dustCoverage: number;
    solarKw: number;
    generationKw: number;
    loadKw: number;
    supplyRatio: number;
  };
  eclss: {
    o2AtmKg: number;
    o2TankKg: number;
    o2TankMaxKg: number;
    co2Kg: number;
    waterL: number;
    waterMaxL: number;
    h2Kg: number;
  };
  thermal: {
    habTempK: number;
    targetK: number;
    radiatorM2: number;
    radiatorBaseM2: number;
    louverPct: number;
    heaterKw: number;
    heaterMaxKw: number;
  };
  food: { kcal: number; cropHealth: number };
  shielding: { regolithCm: number };
  controls: Controls;
  crew: CrewMember[];
  events: ActiveEvent[];
  flags: Record<string, boolean>;
  causeLog: CauseEntry[];
  history: HistoryPoint[];
  nextHistorySimSec: number;
  scheduledDone: number[];
  earth: {
    pending: { deliverAtTick: number; text: string } | null;
    inbox: EarthMessage[];
  };
}

export type Action =
  | { type: 'SET_SYSTEM'; system: SystemName; on: boolean }
  | { type: 'SET_RADIATOR'; louverPct: number }
  | { type: 'SET_HEATER'; maxKw: number }
  | { type: 'CLEAN_PANELS' }
  | { type: 'ADD_SHIELDING' }
  | { type: 'REPAIR_RADIATOR' }
  | { type: 'REQUEST_EARTH_ADVICE' };
''',
    'src/main.tsx': r'''import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './client/App.tsx';
import './client/styles.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
''',
    'tests/engine/balance.test.ts': r'''import { describe, expect, it } from 'vitest';
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
''',
    'tests/engine/debrief.test.ts': r'''import { describe, expect, it } from 'vitest';
import { buildDebrief } from '../../src/engine/debrief.ts';
import { idlePolicy, sabotagePolicy } from '../../src/engine/policies.ts';
import { runMission } from './helpers.ts';

describe('debrief', () => {
  it('links crises to earlier causes and teaches a lesson', () => {
    const d = buildDebrief(runMission('mars-dust-storm', 4, sabotagePolicy).getState());
    expect(d.outcome).toBe('FAILED');
    expect(d.chains.length).toBeGreaterThan(0);
    expect(d.chains.some((c) => c.causes.length > 0)).toBe(true);
    expect(d.lessons.length).toBeGreaterThan(0);
    expect(d.score).toBeLessThan(40);
  });

  it('scores are between 0 and 100', () => {
    const d = buildDebrief(runMission('moon-lunar-night', 2, idlePolicy).getState());
    expect(d.score).toBeGreaterThanOrEqual(0);
    expect(d.score).toBeLessThanOrEqual(100);
  });
});
''',
    'tests/engine/determinism.test.ts': r'''import { describe, expect, it } from 'vitest';
import { SimulationEngine } from '../../src/engine/SimulationEngine.ts';
import { competentPolicy } from '../../src/engine/policies.ts';
import { runMission } from './helpers.ts';

describe('determinism', () => {
  it('same scenario, seed and policy give identical results', () => {
    const a = runMission('mars-dust-storm', 7, competentPolicy).getState();
    const b = runMission('mars-dust-storm', 7, competentPolicy).getState();
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });

  it('different seeds give different runs', () => {
    const a = runMission('mars-dust-storm', 1, competentPolicy).getState();
    const b = runMission('mars-dust-storm', 2, competentPolicy).getState();
    expect(JSON.stringify(a)).not.toEqual(JSON.stringify(b));
  });

  it('save and restore continues exactly like an uninterrupted run', () => {
    const full = new SimulationEngine('moon-lunar-night', 3);
    const half = new SimulationEngine('moon-lunar-night', 3);
    for (let i = 0; i < 1500; i++) { full.step(); half.step(); }
    const restored = new SimulationEngine('moon-lunar-night', 3, half.getState());
    for (let i = 0; i < 1500; i++) { full.step(); restored.step(); }
    expect(JSON.stringify(restored.getState())).toBe(JSON.stringify(full.getState()));
  });
});
''',
    'tests/engine/helpers.ts': r'''import { SimulationEngine } from '../../src/engine/SimulationEngine.ts';
import type { Policy } from '../../src/engine/policies.ts';

/** Runs a mission to the end (or a tick limit) with an optional policy. */
export function runMission(scenarioId: string, seed: number, policy?: Policy, maxTicks = 20000): SimulationEngine {
  const e = new SimulationEngine(scenarioId, seed);
  let n = 0;
  while (e.peek().status === 'ACTIVE' && n++ < maxTicks) {
    if (policy) for (const a of policy(e.peek())) e.dispatch(a);
    e.step();
  }
  return e;
}
''',
    'tests/engine/physics.test.ts': r'''import { describe, expect, it } from 'vitest';
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
''',
}

# ---------------------------------------------------------------------------
# 2. AGENT DOCUMENTS
# ---------------------------------------------------------------------------
AGENTS_MD = r"""# Instructions for AI agents working on Ares Horizon

Goal: finish a working, tested, documented, free-to-host simulator for running a crewed Mars or Moon outpost
(NASA Space Apps Challenge). Four undergraduate students own this project; their name goes on it.

## Loop

1. `python scripts/ares_setup.py next` prints your task. Read it fully.
2. Do the work in small steps. Commit after each meaningful step (`type: summary`, for example `feat: add quiz`).
3. `python scripts/ares_setup.py verify` must show no FAIL before you stop.
4. `python scripts/ares_setup.py done <ID>` marks the task done only if verify and the task's own check pass.
5. Repeat until `python scripts/ares_setup.py status` says all required tasks are done.

## Ground rules

1. Keep `src/engine` pure: no DOM, no React, no timers, no `Math.random`, no `Date`, no `localStorage`.
   Randomness only through `nextFloat(state)`. The verify gate enforces this.
2. Never weaken, skip or delete a test to make it pass. Fix the code. If a balance number changes on purpose,
   change the threshold in the same commit and say why in the commit message.
3. Free only. No paid APIs, no paid hosting, no secrets or keys in the repository. Public keys (for example a Supabase
   anon key) go in environment variables documented in `.env.example`.
4. Do not invent facts or citations. If you cannot verify a number from a real source, leave `TODO` in
   `docs/SOURCES.md` and say so in your final message.
5. Do not claim results that were not measured (users, performance, learning gains). Write what was actually done.
6. The UI holds no game rules. Rules live in `src/engine` and are covered by tests.
7. Accessibility floor: keyboard reachable controls, visible focus, no colour-only status, `prefers-reduced-motion`
   respected, text contrast of at least 4.5:1.
8. Prefer small, readable code over clever code. These are students who must be able to explain every file.

## Repo map

- `src/engine/` simulation (constants, scenarios, engine, crew, events, debrief, policies, telemetry)
- `src/client/` React UI, Web Worker, persistence
- `tests/engine/` unit, determinism, balance and debrief tests
- `docs/` architecture, sources, playtest log, blueprint (roadmap), smoke test
- `agent/` task progress and verify report (generated)

## Commands

- `npm run dev` start the game, `npm test` run tests, `npm run typecheck`, `npm run build`
- `python scripts/ares_setup.py verify` all gates, `... tasks`, `... next`, `... done <ID>`, `... status`

## Definition of done for the whole project

All required tasks done, CI green on GitHub, game live on GitHub Pages, `docs/SOURCES.md` without TODO,
README with screenshots and an honest implemented-versus-planned table, tag `v1.0.0`.
"""

SMOKE_TEST_MD = """# Manual smoke test (task T02)

Run `npm run dev`, open the printed address in Chrome, and tick each item only after you have seen it work.
Write bugs you find under "Bugs" with how you fixed them.

- [ ] Setup screen shows both missions and the seed box
- [ ] Start Mars mission: gauges move, the Sol counter advances about once a minute at 1x
- [ ] Speed buttons (Pause, 1x, 2x, 5x) change the pace; Pause really stops time
- [ ] Around Sol 2 the dust storm starts: alert chip appears, battery falls faster
- [ ] Toggling a system changes the power load and logs an entry in the mission log
- [ ] Radiator louver and heater sliders change cabin temperature over time
- [ ] Ask Earth for advice: button waits, the reply appears after the delay
- [ ] Crew cards show health, stress and dose; a lost crew member is greyed out
- [ ] Mission ends (let it run at 5x): debrief shows outcome, score, causes and lessons
- [ ] Download run data produces a JSON file
- [ ] Play this mission again starts a fresh run with the same seed
- [ ] Reload the page mid-mission: Continue saved mission restores it
- [ ] Moon mission runs and the sun sets about five days in
- [ ] Keyboard only: Tab reaches every control with a visible focus ring
- [ ] No red errors in the browser console during a full run

## Bugs found and fixed

(none yet)
"""

BLUEPRINT_STUB = """# Blueprint (target architecture and roadmap)

The original enterprise blueprint was not supplied during scaffolding.
Re-run with `python ares_setup.py scaffold --force --blueprint path/to/blueprint.md`
or copy it here by hand.
"""

BLUEPRINT_NOTE = """> **Status of this document.** This is the long-term target architecture and roadmap.
> The implemented game is a free, browser-only slice of it. See README.md for what is built today.
> Targets in this file (user counts, uptime, latency, learning gains) are goals, not measured results.

"""

# ---------------------------------------------------------------------------
# 3. AGENT TASK QUEUE (single source of truth; rendered to docs/TASKS.md)
# ---------------------------------------------------------------------------
TASKS = [
    {
        "id": "T01", "required": True,
        "title": "Install dependencies and get every gate green",
        "why": "Proves the generated baseline works on this machine before anything is changed.",
        "steps": [
            "Run: python scripts/ares_setup.py install",
            "Run: python scripts/ares_setup.py verify",
            "If a gate fails, read agent/verify-report.md, fix the cause (not the test), and re-run.",
            "Commit package-lock.json (CI needs it for npm ci).",
        ],
        "done_when": ["verify shows no FAIL"],
    },
    {
        "id": "T02", "required": True,
        "title": "Smoke-test the game in a real browser",
        "why": "Unit tests do not cover the UI. A human-style walkthrough finds layout and worker bugs.",
        "steps": [
            "Run: npm run dev and open the printed address in Chrome.",
            "Work through docs/SMOKE_TEST.md and tick each item only after seeing it work.",
            "Fix every bug you find. Add an engine test when the bug was in the rules.",
            "Record bugs and fixes at the bottom of docs/SMOKE_TEST.md.",
        ],
        "done_when": ["docs/SMOKE_TEST.md has no unticked boxes", "verify shows no FAIL"],
    },
    {
        "id": "T03", "required": True,
        "title": "Create the GitHub repository, CI and free hosting",
        "why": "Gives the team a public repo, a green CI badge and a live link for the supervisor.",
        "steps": [
            "Create an empty public repo on GitHub (no README). Add all four teammates as collaborators.",
            "Run: git remote add origin <repo-url> and git push -u origin main",
            "In the repo: Settings > Pages > Build and deployment > Source = GitHub Actions.",
            "Wait for the CI and Deploy to GitHub Pages workflows to go green in the Actions tab.",
            "Put the live link in README.md (replace the placeholder under Live demo) and add a CI badge.",
        ],
        "done_when": ["git remote 'origin' exists", "README.md no longer contains the placeholder demo link"],
    },
    {
        "id": "T04", "required": True,
        "title": "Verify every number and cite real sources",
        "why": "Credibility. The challenge asks for real trade-offs, so each value needs a source or an honest ASSUMPTION label.",
        "steps": [
            "Open docs/SOURCES.md. For each row marked TODO, find the real NASA (or other agency) page or paper.",
            "Search for: NASA Baseline Values and Assumptions Document (BVAD); NASA Mars fact sheet; NASA Moon fact sheet; "
            "Curiosity RAD dose; Kilopower project.",
            "Put the real URL in the Source column and set Status to verified, or to ASSUMPTION with a reason.",
            "If a verified value differs from the code, update src/engine/constants.ts or scenarios.ts, then re-run tests and "
            "re-balance (see T05). Never invent a link.",
        ],
        "done_when": ["docs/SOURCES.md contains no TODO", "verify shows no FAIL"],
    },
    {
        "id": "T05", "required": True,
        "title": "Playtest and balance the game",
        "why": "A game that is too easy or impossible teaches nothing. Evidence from real players is what a supervisor trusts.",
        "steps": [
            "Get at least 5 different people to play a full mission without help. Observe silently.",
            "Log each session in docs/PLAYTEST.md (no names).",
            "Fix the top three confusions (copy, controls, hints). Retune scenario numbers if needed.",
            "Keep tests/engine/balance.test.ts passing: competent wins, idle loses crew, sabotage always fails.",
            "Fill the Summary section of docs/PLAYTEST.md with what changed and why.",
        ],
        "done_when": ["docs/PLAYTEST.md has at least 5 session rows", "verify shows no FAIL"],
    },
    {
        "id": "T06", "required": True,
        "title": "Add a pre- and post-mission learning quiz",
        "why": "Measures whether players learned. This is the evaluation evidence for the project.",
        "steps": [
            "Create src/client/quiz.ts with 3 multiple-choice questions on coupled systems, for example: why a dust storm "
            "threatens oxygen; what the Sabatier reactor recovers; why shielding should be built before a solar event.",
            "Create src/client/components/Quiz.tsx. Show it before the mission and again on the debrief screen.",
            "Store before/after answers in localStorage and include them in the downloaded run JSON.",
            "Keep it accessible: radio groups with labels, keyboard operable, no colour-only feedback.",
            "Add a unit test for the scoring function.",
        ],
        "done_when": ["src/client/quiz.ts and src/client/components/Quiz.tsx exist", "verify shows no FAIL"],
    },
    {
        "id": "T07", "required": True,
        "title": "Add a short tutorial and run an accessibility pass",
        "why": "Young learners need guidance in the first minute, and the design promises accessibility.",
        "steps": [
            "Create src/client/components/Tutorial.tsx: a dismissible 4-step overlay (goal, gauges, systems, Ask Earth).",
            "Show it on first visit only (remember in localStorage) with a 'Show tutorial' button in the top bar.",
            "Check keyboard-only play, focus order, aria labels, reduced motion and contrast (4.5:1 minimum).",
            "Write what you checked and fixed in docs/ACCESSIBILITY.md.",
        ],
        "done_when": ["src/client/components/Tutorial.tsx and docs/ACCESSIBILITY.md exist", "verify shows no FAIL"],
    },
    {
        "id": "T08", "required": True,
        "title": "Add a third mission",
        "why": "Shows the engine is data-driven and gives the supervisor a visible extension.",
        "steps": [
            "Add a scenario to SCENARIOS in src/engine/scenarios.ts, for example a Mars crew-of-6 mission with a "
            "scheduled solar particle event, or a Moon mission starting at lunar dawn.",
            "Make sure competentPolicy still wins and idle still loses crew. Tune the numbers, not the thresholds.",
            "Document the new scenario in README.md.",
        ],
        "done_when": ["scenarios.ts defines at least 3 scenarios", "verify shows no FAIL"],
    },
    {
        "id": "T09", "required": True,
        "title": "Grow the test suite and add coverage",
        "why": "A tested engine is the strongest software-engineering evidence on the GitHub repo.",
        "steps": [
            "Run: npm i -D @vitest/coverage-v8 and then: npx vitest run --coverage",
            "Add tests until the engine has at least 35 test cases and line coverage above 85 percent. Cover each event, "
            "crew death, every advice rule, every crisis code, save/restore and each Action type.",
            "Add a 'test:coverage' script to package.json and show the coverage number in the README.",
        ],
        "done_when": ["tests contain at least 35 it( cases", "verify shows no FAIL"],
    },
    {
        "id": "T10", "required": True,
        "title": "Polish the repository and release v1.0.0",
        "why": "The repo is the portfolio piece.",
        "steps": [
            "Take 3 screenshots (setup, mission HUD during a crisis, debrief) and save them in docs/img/. Add them to README.md.",
            "Record a 2-minute demo with OBS Studio (free) or the OS screen recorder; link it in README.md.",
            "Fill the Team section of README.md with names, roles and what each person built.",
            "Update the implemented-versus-planned table so it is accurate.",
            "Tag the release: git tag v1.0.0 and git push --tags. Create a GitHub Release with notes.",
        ],
        "done_when": ["README.md has no '(fill in' markers", "git tag v1.0.0 exists"],
    },
    {
        "id": "T11", "required": True,
        "title": "Write the pitch pack for the supervisor",
        "why": "Turns the work into the story that answers the supervisor's feedback on novelty and scope.",
        "steps": [
            "Create docs/PITCH.md with: Problem, Gap in existing tools, Solution, Novelty (coupled systems, crew stress, "
            "signal delay, causal debrief, deterministic classroom seeds), Technical scope, Evaluation (real playtest "
            "numbers from docs/PLAYTEST.md and the quiz), Risks and limits, Phase 2 roadmap from docs/BLUEPRINT.md.",
            "Use only measured results. State limits honestly.",
            "Add a 2-minute demo script: what to click, in what order, and what to say.",
            "Keep it under two pages.",
        ],
        "done_when": ["docs/PITCH.md exists, has at least 250 words and no TODO"],
    },
    {
        "id": "T12", "required": False,
        "title": "Optional: classroom mode on the free Supabase tier",
        "why": "Phase 2 scope: a teacher shares a class code and sees results. Check Supabase's current free-tier limits first.",
        "steps": [
            "Create a free Supabase project. Write supabase/schema.sql with tables classes(code, created_at) and "
            "runs(id, class_code, call_sign, scenario_id, seed, outcome, score, sols, survivors, created_at).",
            "Enable row level security: anonymous insert on runs, select only for a matching class code. No personal data, call signs only.",
            "Add src/client/classroom/ with a join-by-code screen and a /?teacher=CODE results table.",
            "Read the URL and anon key from VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY (document in .env.example). "
            "Never commit the service role key.",
            "Write docs/CLASSROOM.md with setup steps. The game must still work fully offline without Supabase.",
        ],
        "done_when": ["supabase/schema.sql and docs/CLASSROOM.md exist", "verify shows no FAIL"],
    },
    {
        "id": "T13", "required": False,
        "title": "Optional: isometric PixiJS outpost view",
        "why": "A richer visual for the demo. Only after every required task is done.",
        "steps": [
            "Run: npm i pixi.js",
            "Add src/client/components/IsoMap.tsx that draws the six modules on an isometric grid and animates power flow.",
            "Keep OutpostMap.tsx as the fallback and add a toggle. Respect prefers-reduced-motion.",
            "Keep the 60 FPS target on a low-end laptop and note how you measured it.",
        ],
        "done_when": ["package.json lists pixi.js", "verify shows no FAIL"],
    },
]

# ---------------------------------------------------------------------------
# 4. HELPERS
# ---------------------------------------------------------------------------


def info(msg: str = "") -> None:
    print(msg, flush=True)


def run(cmd: str, cwd: Path, capture: bool = False) -> "tuple[int, str]":
    """Run a shell command. Returns (exit code, combined output when capture=True)."""
    try:
        if capture:
            p = subprocess.run(cmd, cwd=str(cwd), shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, universal_newlines=True, encoding="utf-8", errors="replace")
            return p.returncode, p.stdout or ""
        p = subprocess.run(cmd, cwd=str(cwd), shell=True)
        return p.returncode, ""
    except FileNotFoundError as exc:
        return 127, str(exc)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def resolve_root(dir_arg: "str | None", for_scaffold: bool) -> Path:
    if dir_arg:
        return Path(dir_arg).expanduser().resolve()
    here = Path(__file__).resolve().parent
    if here.name == "scripts" and (here.parent / "package.json").exists():
        return here.parent
    cwd = Path.cwd()
    if (cwd / "package.json").exists() and (cwd / "src" / "engine").exists():
        return cwd
    return (cwd / PROJECT_NAME).resolve()


def progress_path(root: Path) -> Path:
    return root / "agent" / "progress.json"


def load_progress(root: Path) -> dict:
    p = progress_path(root)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def save_progress(root: Path, data: dict) -> None:
    write_text(progress_path(root), json.dumps(data, indent=2) + "\n")


def render_tasks_md() -> str:
    out = ["# Agent task queue", "",
           "Generated by `python scripts/ares_setup.py scaffold`. Work in order. "
           "Use `python scripts/ares_setup.py next` for a ready-to-paste prompt.", ""]
    for t in TASKS:
        out.append("## %s: %s%s" % (t["id"], t["title"], "" if t["required"] else " (optional)"))
        out.append("")
        out.append("Why: " + t["why"])
        out.append("")
        out.append("Steps:")
        for i, s in enumerate(t["steps"], 1):
            out.append("%d. %s" % (i, s))
        out.append("")
        out.append("Done when:")
        for d in t["done_when"]:
            out.append("- " + d)
        out.append("")
        out.append("Finish with: `python scripts/ares_setup.py done %s`" % t["id"])
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 5. COMMANDS
# ---------------------------------------------------------------------------


def cmd_scaffold(root: Path, force: bool, blueprint: "str | None") -> int:
    if (root / "package.json").exists() and not force:
        info("A project already exists at %s. Use --force to overwrite it." % root)
        return 1
    info("Scaffolding Ares Horizon into %s" % root)
    for rel, content in FILES.items():
        write_text(root.joinpath(*rel.split("/")), content)
    write_text(root / "AGENTS.md", AGENTS_MD)
    write_text(root / "docs" / "TASKS.md", render_tasks_md())
    write_text(root / "docs" / "SMOKE_TEST.md", SMOKE_TEST_MD)
    bp = BLUEPRINT_STUB
    if blueprint:
        bp_path = Path(blueprint).expanduser()
        if bp_path.exists():
            bp = BLUEPRINT_NOTE + bp_path.read_text(encoding="utf-8")
            info("  copied blueprint into docs/BLUEPRINT.md")
        else:
            info("  blueprint file not found: %s (wrote a stub instead)" % blueprint)
    write_text(root / "docs" / "BLUEPRINT.md", bp)
    me = Path(__file__).resolve()
    target = root / "scripts" / "ares_setup.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    if me != target.resolve():
        shutil.copyfile(str(me), str(target))
    if not progress_path(root).exists():
        save_progress(root, {t["id"]: "pending" for t in TASKS})
    info("  wrote %d project files plus AGENTS.md, docs and scripts/ares_setup.py" % len(FILES))
    return 0


def cmd_install(root: Path) -> int:
    if not (root / "package.json").exists():
        info("No project at %s. Run scaffold first." % root)
        return 1
    info("Installing dependencies (npm install). This needs internet once.")
    code, _ = run("npm install --no-audit --no-fund", root)
    if code != 0:
        info("npm install failed. Check your internet connection and that Node.js 18+ is installed.")
    return code


def _node_major() -> int:
    code, out = run("node --version", Path.cwd(), capture=True)
    m = re.search(r"v(\d+)\.", out or "")
    return int(m.group(1)) if code == 0 and m else 0


REQUIRED_FILES = [
    "package.json", "tsconfig.json", "vite.config.ts", "index.html", "README.md", "AGENTS.md",
    "src/main.tsx", "src/client/App.tsx", "src/client/styles.css", "src/client/workers/sim.worker.ts",
    "src/engine/SimulationEngine.ts", "src/engine/constants.ts", "src/engine/scenarios.ts",
    "src/engine/debrief.ts", "src/engine/policies.ts", "src/engine/rng.ts", "src/engine/types.ts",
    "tests/engine/determinism.test.ts", "tests/engine/physics.test.ts", "tests/engine/balance.test.ts",
    "tests/engine/debrief.test.ts", ".github/workflows/ci.yml", ".github/workflows/pages.yml",
    "docs/ARCHITECTURE.md", "docs/SOURCES.md", "docs/PLAYTEST.md", "docs/TASKS.md",
]

PURITY_FORBIDDEN = [
    "Math.random", "Date.now", "new Date", "document.", "window.", "localStorage", "sessionStorage",
    "setInterval", "setTimeout", "requestAnimationFrame", "from 'react'", 'from "react"', "performance.now",
]

SECRET_PATTERNS = [r"service_role", r"BEGIN (RSA |EC )?PRIVATE KEY", r"AKIA[0-9A-Z]{16}", r"sk-[A-Za-z0-9]{20,}"]


def _gate(results: list, name: str, status: str, detail: str = "") -> None:
    results.append({"name": name, "status": status, "detail": detail})
    tag = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}[status]
    info("%s %s%s" % (tag, name, (" - " + detail) if detail else ""))


def _tail(text: str, n: int = 25) -> str:
    return "\n".join(text.strip().splitlines()[-n:])


def cmd_verify(root: Path, quiet: bool = False) -> int:
    results: list = []
    info("Verifying %s" % root)
    major = _node_major()
    _gate(results, "Node.js 18 or newer", "PASS" if major >= 18 else "FAIL",
          "found major version %d" % major if major else "node not found: install from nodejs.org")
    code, _ = run("npm --version", root, capture=True)
    _gate(results, "npm available", "PASS" if code == 0 else "FAIL")

    missing = [f for f in REQUIRED_FILES if not (root / f).exists()]
    _gate(results, "Required files present", "FAIL" if missing else "PASS", ", ".join(missing[:6]) + (" ..." if len(missing) > 6 else ""))

    # Engine purity: the engine must stay deterministic and UI-free.
    offenders = []
    engine_dir = root / "src" / "engine"
    if engine_dir.exists():
        for f in engine_dir.rglob("*.ts"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for token in PURITY_FORBIDDEN:
                if token in text:
                    offenders.append("%s uses %s" % (f.relative_to(root).as_posix(), token))
    _gate(results, "Engine purity (no DOM, timers, Math.random, Date)", "FAIL" if offenders else "PASS", "; ".join(offenders[:4]))

    installed = (root / "node_modules" / ".bin").exists()
    _gate(results, "Dependencies installed", "PASS" if installed else "FAIL", "" if installed else "run: python scripts/ares_setup.py install")
    if installed:
        for name, cmd in (("TypeScript typecheck", "npm run typecheck"), ("Tests", "npm test"), ("Production build", "npm run build")):
            code, out = run(cmd, root, capture=True)
            _gate(results, name, "PASS" if code == 0 else "FAIL", "" if code == 0 else "\n" + _tail(out))

    # Advisory checks (warnings only)
    src = root / "docs" / "SOURCES.md"
    if src.exists():
        n = src.read_text(encoding="utf-8").count("TODO")
        _gate(results, "docs/SOURCES.md fully cited", "PASS" if n == 0 else "WARN", "" if n == 0 else "%d TODO markers left (task T04)" % n)
    readme = root / "README.md"
    if readme.exists():
        n = readme.read_text(encoding="utf-8").count("(fill in")
        _gate(results, "README placeholders filled", "PASS" if n == 0 else "WARN", "" if n == 0 else "%d '(fill in' markers left" % n)
    hits = []
    for base in ("src", "docs", "tests"):
        for f in (root / base).rglob("*") if (root / base).exists() else []:
            if f.is_file() and f.suffix in (".ts", ".tsx", ".md", ".json", ".html", ".css"):
                t = f.read_text(encoding="utf-8", errors="replace")
                if any(re.search(p, t) for p in SECRET_PATTERNS) and f.name != "ares_setup.py":
                    hits.append(f.relative_to(root).as_posix())
    _gate(results, "No secrets in the repository", "FAIL" if hits else "PASS", ", ".join(hits))
    code, out = run("git rev-parse --is-inside-work-tree", root, capture=True)
    _gate(results, "Git repository", "PASS" if code == 0 else "WARN", "" if code == 0 else "run: git init (or use `all`)")

    fails = [r for r in results if r["status"] == "FAIL"]
    warns = [r for r in results if r["status"] == "WARN"]
    lines = ["# Verify report", "", "Failures: %d, warnings: %d" % (len(fails), len(warns)), ""]
    for r in results:
        lines.append("- **%s** %s%s" % (r["status"], r["name"], (": " + r["detail"].strip()) if r["detail"] else ""))
    write_text(root / "agent" / "verify-report.md", "\n".join(lines) + "\n")
    info("")
    info("RESULT: %s (%d fail, %d warn). Report: agent/verify-report.md" % ("FAIL" if fails else "OK", len(fails), len(warns)))
    return 1 if fails else 0


def cmd_dev(root: Path) -> int:
    info("Starting the dev server. Press Ctrl+C to stop.")
    code, _ = run("npm run dev", root)
    return code


def _git(root: Path, cmd: str) -> "tuple[int, str]":
    return run("git " + cmd, root, capture=True)


def cmd_git_init(root: Path) -> None:
    if shutil.which("git") is None:
        info("git not found: skipping repository setup (install git from git-scm.com).")
        return
    if not (root / ".git").exists():
        code, _ = _git(root, "init -b main")
        if code != 0:
            _git(root, "init")
            _git(root, "checkout -b main")
    _git(root, "add -A")
    code, out = _git(root, 'commit -m "chore: scaffold Ares Horizon with tested simulation engine"')
    if code == 0:
        info("Created the first commit.")
    else:
        info("Commit skipped. If git asked who you are, run:")
        info('  git config --global user.name "Your Name"')
        info('  git config --global user.email "you@example.com"')
        info("then: git add -A && git commit -m \"chore: scaffold\"")


# ---- task checks (objective acceptance tests per task) --------------------

def _read(root: Path, rel: str) -> str:
    p = root / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def check_task(root: Path, tid: str) -> "tuple[bool, str]":
    if tid == "T02":
        t = _read(root, "docs/SMOKE_TEST.md")
        left = len(re.findall(r"- \[ \]", t))
        return (left == 0 and bool(t), "%d smoke-test boxes still unticked" % left)
    if tid == "T03":
        code, _ = _git(root, "remote get-url origin")
        placeholder = "(fill in: GitHub Pages link" in _read(root, "README.md")
        return (code == 0 and not placeholder, "needs a git remote 'origin' and the live link in README.md")
    if tid == "T04":
        n = _read(root, "docs/SOURCES.md").count("TODO")
        return (n == 0, "%d TODO markers remain in docs/SOURCES.md" % n)
    if tid == "T05":
        rows = 0
        for line in _read(root, "docs/PLAYTEST.md").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 8 and cells[0] and cells[0] not in ("Player",) and not set(cells[0]) <= set("-: "):
                rows += 1
        return (rows >= 5, "found %d playtest rows, need at least 5" % rows)
    if tid == "T06":
        ok = (root / "src/client/quiz.ts").exists() and (root / "src/client/components/Quiz.tsx").exists()
        return (ok, "create src/client/quiz.ts and src/client/components/Quiz.tsx")
    if tid == "T07":
        ok = (root / "src/client/components/Tutorial.tsx").exists() and (root / "docs/ACCESSIBILITY.md").exists()
        return (ok, "create Tutorial.tsx and docs/ACCESSIBILITY.md")
    if tid == "T08":
        n = len(re.findall(r"^\s{4}id: '", _read(root, "src/engine/scenarios.ts"), flags=re.M))
        return (n >= 3, "found %d scenarios, need at least 3" % n)
    if tid == "T09":
        n = 0
        tests = root / "tests"
        for f in tests.rglob("*.test.ts") if tests.exists() else []:
            n += len(re.findall(r"\bit\(", f.read_text(encoding="utf-8", errors="replace")))
        return (n >= 35, "found %d it( cases, need at least 35" % n)
    if tid == "T10":
        placeholder = _read(root, "README.md").count("(fill in")
        code, out = _git(root, "tag --list v1.0.0")
        return (placeholder == 0 and "v1.0.0" in out, "README placeholders: %d; tag v1.0.0 %s" % (placeholder, "found" if "v1.0.0" in out else "missing"))
    if tid == "T11":
        t = _read(root, "docs/PITCH.md")
        words = len(t.split())
        return (words >= 250 and "TODO" not in t, "docs/PITCH.md has %d words (need 250+, no TODO)" % words)
    if tid == "T12":
        ok = (root / "supabase/schema.sql").exists() and (root / "docs/CLASSROOM.md").exists()
        return (ok, "create supabase/schema.sql and docs/CLASSROOM.md")
    if tid == "T13":
        return ("pixi.js" in _read(root, "package.json"), "pixi.js is not in package.json")
    return (True, "")


def _task_by_id(tid: str) -> "dict | None":
    for t in TASKS:
        if t["id"].upper() == tid.upper():
            return t
    return None


def _next_task(root: Path) -> "dict | None":
    prog = load_progress(root)
    pending = [t for t in TASKS if prog.get(t["id"]) != "done"]
    required = [t for t in pending if t["required"]]
    return (required or pending or [None])[0]


def cmd_tasks(root: Path) -> int:
    prog = load_progress(root)
    for t in TASKS:
        mark = "[x]" if prog.get(t["id"]) == "done" else "[ ]"
        info("%s %s  %s%s" % (mark, t["id"], t["title"], "" if t["required"] else "  (optional)"))
    return 0


def cmd_status(root: Path) -> int:
    prog = load_progress(root)
    req = [t for t in TASKS if t["required"]]
    done = [t for t in req if prog.get(t["id"]) == "done"]
    info("Required tasks done: %d of %d" % (len(done), len(req)))
    nxt = _next_task(root)
    if nxt and not (len(done) == len(req)):
        info("Next: %s %s" % (nxt["id"], nxt["title"]))
    elif len(done) == len(req):
        info("All required tasks are done. Optional: T12 classroom mode, T13 PixiJS view.")
    return 0


def prompt_for(root: Path, t: dict) -> str:
    lines = [
        "=== TASK %s: %s ===" % (t["id"], t["title"]),
        "You are an AI engineer working in the repository at: %s" % root,
        "First read AGENTS.md (ground rules) and docs/ARCHITECTURE.md.",
        "",
        "Why this task matters: " + t["why"],
        "",
        "Steps:",
    ]
    for i, s in enumerate(t["steps"], 1):
        lines.append("  %d. %s" % (i, s))
    lines += ["", "Done when:"]
    for d in t["done_when"]:
        lines.append("  - " + d)
    lines += [
        "",
        "Before you stop: python scripts/ares_setup.py verify  (no FAIL allowed)",
        "Then run:        python scripts/ares_setup.py done %s" % t["id"],
        "Report: what you changed, what you could not verify, and anything a human must do (for example GitHub login).",
    ]
    return "\n".join(lines)


def cmd_next(root: Path) -> int:
    t = _next_task(root)
    if t is None:
        info("Every task is done.")
        return 0
    text = prompt_for(root, t)
    write_text(root / "agent" / "CURRENT_TASK.md", text + "\n")
    info(text)
    info("")
    info("(also saved to agent/CURRENT_TASK.md)")
    return 0


def cmd_done(root: Path, tid: str, force: bool) -> int:
    t = _task_by_id(tid)
    if t is None:
        info("Unknown task id: %s" % tid)
        return 1
    if not force:
        if cmd_verify(root) != 0:
            info("Task %s NOT marked done: fix the failing gates first." % t["id"])
            return 1
        ok, msg = check_task(root, t["id"])
        if not ok:
            info("Task %s NOT marked done: %s" % (t["id"], msg))
            return 1
    prog = load_progress(root)
    prog[t["id"]] = "done"
    save_progress(root, prog)
    info("Task %s marked done." % t["id"])
    nxt = _next_task(root)
    if nxt:
        info("Next up: %s %s  (run: python scripts/ares_setup.py next)" % (nxt["id"], nxt["title"]))
    return 0


def cmd_all(root: Path, force: bool, blueprint: "str | None") -> int:
    if cmd_scaffold(root, force, blueprint) != 0:
        return 1
    if cmd_install(root) != 0:
        return 1
    cmd_git_init(root)
    code = cmd_verify(root)
    info("")
    info("Done. Project folder: %s" % root)
    info("Play it:        cd %s && npm run dev" % root)
    info("Agent tasks:    python scripts/ares_setup.py next")
    return code


def main(argv: "list | None" = None) -> int:
    ap = argparse.ArgumentParser(description="Ares Horizon setup, verification and AI-agent task runner")
    ap.add_argument("command", choices=["all", "scaffold", "install", "verify", "dev", "tasks", "next", "done", "status"])
    ap.add_argument("task_id", nargs="?", help="task id for the done command, for example T04")
    ap.add_argument("--dir", help="project folder (default: ./ares-horizon)")
    ap.add_argument("--blueprint", help="path to your blueprint .md file")
    ap.add_argument("--force", action="store_true", help="overwrite (scaffold) or skip checks (done)")
    a = ap.parse_args(argv)
    root = resolve_root(a.dir, a.command in ("all", "scaffold"))

    if a.command == "scaffold":
        return cmd_scaffold(root, a.force, a.blueprint)
    if a.command == "all":
        return cmd_all(root, a.force, a.blueprint)
    if not (root / "package.json").exists():
        info("No project found at %s. Run: python ares_setup.py all" % root)
        return 1
    if a.command == "install":
        return cmd_install(root)
    if a.command == "verify":
        return cmd_verify(root)
    if a.command == "dev":
        return cmd_dev(root)
    if a.command == "tasks":
        return cmd_tasks(root)
    if a.command == "next":
        return cmd_next(root)
    if a.command == "status":
        return cmd_status(root)
    if a.command == "done":
        if not a.task_id:
            info("Usage: python ares_setup.py done T04")
            return 1
        return cmd_done(root, a.task_id, a.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())

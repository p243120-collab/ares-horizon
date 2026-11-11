# Architecture

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

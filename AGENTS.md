# Instructions for AI agents working on Ares Horizon

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

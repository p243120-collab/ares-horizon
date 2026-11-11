=== TASK T02: Smoke-test the game in a real browser ===
You are an AI engineer working in the repository at: C:\Users\Junaid Nawab\Documents\nasa\ares-horizon
First read AGENTS.md (ground rules) and docs/ARCHITECTURE.md.

Why this task matters: Unit tests do not cover the UI. A human-style walkthrough finds layout and worker bugs.

Steps:
  1. Run: npm run dev and open the printed address in Chrome.
  2. Work through docs/SMOKE_TEST.md and tick each item only after seeing it work.
  3. Fix every bug you find. Add an engine test when the bug was in the rules.
  4. Record bugs and fixes at the bottom of docs/SMOKE_TEST.md.

Done when:
  - docs/SMOKE_TEST.md has no unticked boxes
  - verify shows no FAIL

Before you stop: python scripts/ares_setup.py verify  (no FAIL allowed)
Then run:        python scripts/ares_setup.py done T02
Report: what you changed, what you could not verify, and anything a human must do (for example GitHub login).

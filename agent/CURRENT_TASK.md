=== TASK T01: Install dependencies and get every gate green ===
You are an AI engineer working in the repository at: C:\Users\Junaid Nawab\Documents\nasa\ares-horizon
First read AGENTS.md (ground rules) and docs/ARCHITECTURE.md.

Why this task matters: Proves the generated baseline works on this machine before anything is changed.

Steps:
  1. Run: python scripts/ares_setup.py install
  2. Run: python scripts/ares_setup.py verify
  3. If a gate fails, read agent/verify-report.md, fix the cause (not the test), and re-run.
  4. Commit package-lock.json (CI needs it for npm ci).

Done when:
  - verify shows no FAIL

Before you stop: python scripts/ares_setup.py verify  (no FAIL allowed)
Then run:        python scripts/ares_setup.py done T01
Report: what you changed, what you could not verify, and anything a human must do (for example GitHub login).

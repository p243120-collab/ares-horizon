=== TASK T03: Create the GitHub repository, CI and free hosting ===
You are an AI engineer working in the repository at: C:\Users\Junaid Nawab\Documents\nasa\ares-horizon
First read AGENTS.md (ground rules) and docs/ARCHITECTURE.md.

Why this task matters: Gives the team a public repo, a green CI badge and a live link for the supervisor.

Steps:
  1. Create an empty public repo on GitHub (no README). Add all four teammates as collaborators.
  2. Run: git remote add origin <repo-url> and git push -u origin main
  3. In the repo: Settings > Pages > Build and deployment > Source = GitHub Actions.
  4. Wait for the CI and Deploy to GitHub Pages workflows to go green in the Actions tab.
  5. Put the live link in README.md (replace the placeholder under Live demo) and add a CI badge.

Done when:
  - git remote 'origin' exists
  - README.md no longer contains the placeholder demo link

Before you stop: python scripts/ares_setup.py verify  (no FAIL allowed)
Then run:        python scripts/ares_setup.py done T03
Report: what you changed, what you could not verify, and anything a human must do (for example GitHub login).

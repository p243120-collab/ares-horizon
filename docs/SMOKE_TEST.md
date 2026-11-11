# Manual smoke test (task T02)

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

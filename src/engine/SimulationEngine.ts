/**
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

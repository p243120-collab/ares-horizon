/**
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

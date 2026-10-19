/** Defined, concentration-based single-reaction models. No identity or rate prediction. */
export type ActivityMode = 'ideal' | 'entered';
export type EquilibriumConstant = { notation: 'K' | 'pK'; value: number };
export type SpectatorSpecies = {
  name: string;
  charge: number;
  concentration: number;
  activityCoefficient?: number;
};
export type EquilibriumSpecies = {
  name: string;
  side: 'reactant' | 'product';
  coefficient: number;
  phase: 'aq' | 'solid' | 'liquid';
  concentration: number;
  charge: number;
  activityCoefficient?: number;
};
export type EquilibriumModel = {
  species: EquilibriumSpecies[];
  activityMode: ActivityMode;
  balancedConfirmed: boolean;
  /** Fixed, non-reacting dissolved counterions, outside the reaction quotient. */
  spectators?: SpectatorSpecies[];
  temperatureC: number;
};
export type Quotient =
  | { kind: 'finite'; value: number; logValue: number }
  | { kind: 'zero'; value: 0; logValue: number }
  | { kind: 'infinite'; logValue: number; reason: string }
  | { kind: 'undefined'; reason: string };
export type EquilibriumResult = {
  extent: number;
  concentrations: { name: string; phase: EquilibriumSpecies['phase']; concentration?: number }[];
  quotient: Quotient;
  residual: number;
  iterations: number;
};

const LOG_MIN = Math.log(Number.MIN_VALUE);
const LOG_MAX = Math.log(Number.MAX_VALUE);
const RESIDUAL_TOLERANCE = 1e-10;
const MAX_ITERATIONS = 2048;
const nu = (row: EquilibriumSpecies) => row.coefficient * (row.side === 'product' ? 1 : -1);

export function constantLog(constant: EquilibriumConstant): number {
  if (!constant || !['K', 'pK'].includes(constant.notation) || !Number.isFinite(constant.value)) {
    throw new Error('Enter a finite K or pK value.');
  }
  if (constant.notation === 'K' && constant.value <= 0) throw new Error('K must be greater than zero.');
  const result = constant.notation === 'pK' ? -constant.value * Math.LN10 : Math.log(constant.value);
  if (!Number.isFinite(result) || result < LOG_MIN || result > LOG_MAX) {
    throw new Error('The entered constant is outside the supported numeric range.');
  }
  return result;
}

export function validateTemperature(temperatureC: number) {
  if (!Number.isFinite(temperatureC) || temperatureC <= -273.15) {
    throw new Error('Temperature must be finite and above absolute zero.');
  }
}

export function validateSpectators(spectators: SpectatorSpecies[] | undefined, mode: ActivityMode, names = new Set<string>()): { charge: number; scale: number } {
  if (spectators !== undefined && (!Array.isArray(spectators) || spectators.length > 4)) throw new Error('Use at most four fixed spectator species.');
  let charge = 0;
  let scale = 0;
  for (const row of spectators ?? []) {
    if (!row || typeof row.name !== 'string' || !row.name.trim() || row.name.length > 100 || names.has(row.name.trim().toLowerCase())) {
      throw new Error('Spectator species need short, distinct names.');
    }
    names.add(row.name.trim().toLowerCase());
    if (!Number.isInteger(row.charge) || Math.abs(row.charge) > 20) throw new Error('Spectator charges must be integers from −20 to +20.');
    if (!Number.isFinite(row.concentration) || row.concentration < 0) throw new Error('Spectator concentrations must be finite and nonnegative.');
    if (mode === 'entered' && (!Number.isFinite(row.activityCoefficient) || row.activityCoefficient! <= 0)) throw new Error(`Enter a positive activity coefficient for ${row.name}.`);
    const contribution = row.charge * row.concentration;
    charge += contribution;
    scale += Math.abs(contribution);
  }
  if (!Number.isFinite(charge) || !Number.isFinite(scale)) throw new Error('Spectator charge balance overflow.');
  return { charge, scale };
}

export function validateEquilibriumModel(model: EquilibriumModel): void {
  if (!model || !Array.isArray(model.species) || model.species.length < 2 || model.species.length > 12) {
    throw new Error('Enter 2–12 distinct species for one reaction.');
  }
  if (!model.balancedConfirmed) throw new Error('Confirm that the entered equation is atom- and charge-balanced.');
  if (!['ideal', 'entered'].includes(model.activityMode)) throw new Error('Choose an activity mode.');
  validateTemperature(model.temperatureC);
  const names = new Set<string>();
  let reactionCharge = 0;
  let solutionCharge = 0;
  let chargeScale = 0;
  for (const row of model.species) {
    if (!row || typeof row.name !== 'string' || !row.name.trim() || row.name.length > 100) {
      throw new Error('Give every species a short, distinct name.');
    }
    const name = row.name.trim().toLowerCase();
    if (names.has(name)) throw new Error('Combine repeated species into one net stoichiometric row.');
    names.add(name);
    if (!['reactant', 'product'].includes(row.side) || !['aq', 'solid', 'liquid'].includes(row.phase)) {
      throw new Error('Only aqueous species and pure solids/liquids are supported.');
    }
    if (!Number.isInteger(row.coefficient) || row.coefficient < 1 || row.coefficient > 20) {
      throw new Error('Stoichiometric coefficients must be integers from 1 to 20.');
    }
    if (!Number.isInteger(row.charge) || Math.abs(row.charge) > 20) {
      throw new Error('Species charges must be integers from −20 to +20.');
    }
    reactionCharge += nu(row) * row.charge;
    if (row.phase !== 'aq') {
      if (row.charge !== 0) throw new Error('Pure-phase rows must be electrically neutral.');
      continue;
    }
    if (!Number.isFinite(row.concentration) || row.concentration < 0) {
      throw new Error('Aqueous concentrations must be finite and nonnegative.');
    }
    if (model.activityMode === 'entered' && (!Number.isFinite(row.activityCoefficient) || row.activityCoefficient! <= 0)) {
      throw new Error(`Enter a positive activity coefficient for ${row.name}.`);
    }
    const charge = row.charge * row.concentration;
    if (!Number.isFinite(charge)) throw new Error('The charge balance is outside the supported numeric range.');
    solutionCharge += charge;
    chargeScale += Math.abs(charge);
  }
  const spectatorBalance = validateSpectators(model.spectators, model.activityMode, names);
  solutionCharge += spectatorBalance.charge;
  chargeScale += spectatorBalance.scale;
  if (!model.species.some(row => row.side === 'reactant') || !model.species.some(row => row.side === 'product')) {
    throw new Error('Include at least one reactant and one product.');
  }
  if (!model.species.some(row => row.phase === 'aq')) throw new Error('Include at least one dissolved species.');
  if (reactionCharge !== 0) throw new Error('The entered reaction does not conserve charge.');
  if (!Number.isFinite(solutionCharge) || !Number.isFinite(chargeScale)) throw new Error('Charge balance overflow.');
  if (chargeScale === 0 ? solutionCharge !== 0 : Math.abs(solutionCharge / chargeScale) > 1e-10) {
    throw new Error('Concentrations are not electroneutral. Include the fixed spectator counterion charge.');
  }
}

function logQuotient(model: EquilibriumModel, concentrations?: number[]): number | undefined {
  let numeratorZero = false;
  let denominatorZero = false;
  let logValue = 0;
  model.species.forEach((row, index) => {
    if (row.phase !== 'aq') return;
    const concentration = concentrations?.[index] ?? row.concentration;
    if (!Number.isFinite(concentration) || concentration < 0) throw new Error('A concentration became negative or non-finite.');
    if (concentration === 0) {
      if (row.side === 'product') numeratorZero = true;
      else denominatorZero = true;
    } else {
      // Logarithms avoid overflowing gamma*c or concentration powers.
      const logActivity = Math.log(concentration) + (model.activityMode === 'entered' ? Math.log(row.activityCoefficient!) : 0);
      logValue += nu(row) * logActivity;
    }
  });
  if (numeratorZero && denominatorZero) return undefined;
  if (numeratorZero) return -Infinity;
  if (denominatorZero) return Infinity;
  if (!Number.isFinite(logValue)) throw new Error('The reaction quotient is outside the supported numeric range.');
  return logValue;
}

function quotientFromLog(logValue: number | undefined): Quotient {
  if (logValue === undefined) return { kind: 'undefined', reason: 'Both numerator and denominator contain zero concentrations (0/0).' };
  if (logValue === -Infinity) return { kind: 'zero', value: 0, logValue };
  if (logValue === Infinity) return { kind: 'infinite', logValue, reason: 'A reactant concentration is zero; the quotient has a zero denominator.' };
  if (logValue < LOG_MIN || logValue > LOG_MAX) throw new Error('The quotient cannot be represented as a finite number.');
  const value = Math.exp(logValue);
  if (!Number.isFinite(value) || value <= 0) throw new Error('The quotient cannot be represented as a finite number.');
  return { kind: 'finite', value, logValue };
}

export function calculateQuotient(model: EquilibriumModel): Quotient {
  validateEquilibriumModel(model);
  return quotientFromLog(logQuotient(model));
}

export function compareQuotient(quotient: Quotient, constant: EquilibriumConstant): 'forward' | 'reverse' | 'equilibrium' {
  const logK = constantLog(constant);
  if (quotient.kind === 'undefined') throw new Error(`Cannot compare an undefined quotient: ${quotient.reason}`);
  const difference = quotient.logValue - logK;
  return Math.abs(difference) <= RESIDUAL_TOLERANCE ? 'equilibrium' : difference < 0 ? 'forward' : 'reverse';
}

/** c_i = c_i,initial + nu_i*x, at fixed volume and fixed supplied activity coefficients. */
export function solveEquilibrium(model: EquilibriumModel, constant: EquilibriumConstant): EquilibriumResult {
  validateEquilibriumModel(model);
  const logK = constantLog(constant);
  let lower = -Infinity;
  let upper = Infinity;
  let scale = 1e-3;
  model.species.forEach(row => {
    if (row.phase !== 'aq') return;
    const bound = row.concentration / row.coefficient;
    scale = Math.max(scale, bound);
    if (row.side === 'product') lower = Math.max(lower, -bound);
    else upper = Math.min(upper, bound);
  });
  if (!(lower < upper)) throw new Error('No nonzero reaction extent is possible from these initial concentrations.');
  const concentrationsAt = (extent: number) => model.species.map(row => {
    if (row.phase !== 'aq') return 0;
    // The exact positivity endpoint is a true zero, not an invented small concentration.
    const endpoint = -row.concentration / nu(row);
    if (extent === endpoint) return 0;
    const value = row.concentration + nu(row) * extent;
    if (!Number.isFinite(value) || value < 0) throw new Error('A concentration became negative or non-finite.');
    return value;
  });
  const residualAt = (extent: number) => {
    const value = logQuotient(model, concentrationsAt(extent));
    if (value === undefined) throw new Error('The quotient is undefined throughout the available extent interval.');
    return value - logK;
  };
  // Pure phases can make one end unbounded; establish a finite bracket without replacing zeros.
  let lo = Number.isFinite(lower) ? lower : Math.min(0, upper) - scale;
  let hi = Number.isFinite(upper) ? upper : Math.max(0, lower) + scale;
  if (!Number.isFinite(lo) || !Number.isFinite(hi)) throw new Error('Could not form a finite reaction-extent bracket.');
  let fLo = residualAt(lo);
  let fHi = residualAt(hi);
  for (let i = 0; fLo > 0 && i < MAX_ITERATIONS; i++) {
    if (Number.isFinite(lower)) break;
    lo *= 2;
    if (!Number.isFinite(lo)) throw new Error('The equilibrium extent is outside the supported numeric range.');
    fLo = residualAt(lo);
  }
  for (let i = 0; fHi < 0 && i < MAX_ITERATIONS; i++) {
    if (Number.isFinite(upper)) break;
    hi *= 2;
    if (!Number.isFinite(hi)) throw new Error('The equilibrium extent is outside the supported numeric range.');
    fHi = residualAt(hi);
  }
  if (!(fLo <= 0 && fHi >= 0)) throw new Error('No equilibrium root could be bracketed in the allowed concentration range.');
  let extent = 0;
  let residual = Infinity;
  let iterations = 0;
  for (; iterations < MAX_ITERATIONS; iterations++) {
    extent = lo / 2 + hi / 2;
    if (extent === lo || extent === hi) break;
    residual = residualAt(extent);
    if (Math.abs(residual) <= RESIDUAL_TOLERANCE) break;
    if (residual < 0) lo = extent;
    else hi = extent;
  }
  if (!Number.isFinite(residual) || Math.abs(residual) > RESIDUAL_TOLERANCE) {
    throw new Error('The equilibrium solution did not converge at supported numerical precision.');
  }
  const final = concentrationsAt(extent);
  const spectatorBalance = validateSpectators(model.spectators, model.activityMode);
  let netCharge = spectatorBalance.charge;
  let chargeScale = spectatorBalance.scale;
  model.species.forEach((row, index) => {
    if (row.phase !== 'aq') return;
    const expected = row.concentration + nu(row) * extent;
    if (Math.abs(final[index] - expected) > 1e-12 * Math.max(final[index], row.concentration, 1e-300)) {
      throw new Error('The material-balance check failed.');
    }
    netCharge += row.charge * final[index];
    chargeScale += Math.abs(row.charge * final[index]);
  });
  if (!Number.isFinite(netCharge) || !Number.isFinite(chargeScale)
    || (chargeScale === 0 ? netCharge !== 0 : Math.abs(netCharge / chargeScale) > 1e-10)) {
    throw new Error('The final charge-balance check failed.');
  }
  return {
    extent,
    concentrations: model.species.map((row, index) => ({ name: row.name, phase: row.phase,
      ...(row.phase === 'aq' ? { concentration: final[index] } : {}) })),
    quotient: quotientFromLog(logQuotient(model, final)), residual, iterations: iterations + 1,
  };
}

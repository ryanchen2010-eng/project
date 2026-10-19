import { constantLog, validateTemperature, validateSpectators, type ActivityMode, type EquilibriumConstant, type SpectatorSpecies } from './equilibrium-calculator';

export type DissolvedIon = {
  name: string;
  coefficient: number;
  charge: number;
  concentration: number;
  activityCoefficient?: number;
};
export type SolubilityModel = {
  ions: [DissolvedIon, DissolvedIon];
  constant: EquilibriumConstant;
  activityMode: ActivityMode;
  temperatureC: number;
  /** Fixed counterions outside this salt's solubility expression. */
  spectators?: SpectatorSpecies[];
};
export type SaturationResult = {
  quotient: number;
  logQuotient: number;
  status: 'undersaturated' | 'saturated' | 'supersaturated';
};
export type SolubilityResult = {
  solubility: number;
  concentrations: [number, number];
  logResidual: number;
  iterations: number;
};

const TOLERANCE = 1e-10;
const MAX_ITERATIONS = 2048;

export function validateSolubilityModel(model: SolubilityModel): void {
  if (!model || !Array.isArray(model.ions) || model.ions.length !== 2) throw new Error('This model requires exactly two dissolved ion types.');
  if (!['ideal', 'entered'].includes(model.activityMode)) throw new Error('Choose an activity mode.');
  validateTemperature(model.temperatureC);
  constantLog(model.constant);
  const names = new Set<string>();
  let saltCharge = 0;
  let solutionCharge = 0;
  let scale = 0;
  for (const ion of model.ions) {
    if (!ion || typeof ion.name !== 'string' || !ion.name.trim() || ion.name.length > 100 || names.has(ion.name.trim().toLowerCase())) {
      throw new Error('Enter two distinct ion names.');
    }
    names.add(ion.name.trim().toLowerCase());
    if (!Number.isInteger(ion.coefficient) || ion.coefficient < 1 || ion.coefficient > 20) throw new Error('Ion coefficients must be integers from 1 to 20.');
    if (!Number.isInteger(ion.charge) || ion.charge === 0 || Math.abs(ion.charge) > 20) throw new Error('Ion charges must be nonzero integers from −20 to +20.');
    if (!Number.isFinite(ion.concentration) || ion.concentration < 0) throw new Error('Ion concentrations must be finite and nonnegative.');
    if (model.activityMode === 'entered' && (!Number.isFinite(ion.activityCoefficient) || ion.activityCoefficient! <= 0)) {
      throw new Error(`Enter a positive activity coefficient for ${ion.name}.`);
    }
    saltCharge += ion.coefficient * ion.charge;
    solutionCharge += ion.charge * ion.concentration;
    scale += Math.abs(ion.charge * ion.concentration);
  }
  const spectatorBalance = validateSpectators(model.spectators, model.activityMode, names);
  solutionCharge += spectatorBalance.charge;
  scale += spectatorBalance.scale;
  if (saltCharge !== 0 || model.ions[0].charge * model.ions[1].charge >= 0) throw new Error('Ion coefficients and charges must describe one electrically neutral salt.');
  if (!Number.isFinite(solutionCharge) || !Number.isFinite(scale)
    || (scale === 0 ? solutionCharge !== 0 : Math.abs(solutionCharge / scale) > TOLERANCE)) {
    throw new Error('Ion concentrations need balancing spectator counterion rows.');
  }
}

function logProduct(model: SolubilityModel, concentrations: [number, number]): number {
  let sum = 0;
  for (let i = 0; i < 2; i++) {
    const ion = model.ions[i];
    const concentration = concentrations[i];
    if (!Number.isFinite(concentration) || concentration < 0) throw new Error('An ion concentration became negative or non-finite.');
    if (concentration === 0) return -Infinity;
    sum += ion.coefficient * (Math.log(concentration) + (model.activityMode === 'entered' ? Math.log(ion.activityCoefficient!) : 0));
  }
  if (!Number.isFinite(sum)) throw new Error('The ion activity product is outside the supported numeric range.');
  return sum;
}

export function compareSaturation(model: SolubilityModel): SaturationResult {
  validateSolubilityModel(model);
  const logQuotient = logProduct(model, [model.ions[0].concentration, model.ions[1].concentration]);
  const quotient = logQuotient === -Infinity ? 0 : Math.exp(logQuotient);
  if (!Number.isFinite(quotient) || (quotient === 0 && logQuotient !== -Infinity)) {
    throw new Error('Qsp cannot be represented as a finite number.');
  }
  const difference = logQuotient - constantLog(model.constant);
  return { quotient, logQuotient, status: Math.abs(difference) <= TOLERANCE ? 'saturated' : difference < 0 ? 'undersaturated' : 'supersaturated' };
}

/** Additional formula-unit molarity dissolved from excess solid at fixed volume. */
export function calculateSolubility(model: SolubilityModel): SolubilityResult {
  validateSolubilityModel(model);
  const logK = constantLog(model.constant);
  const concentrationsAt = (solubility: number): [number, number] => model.ions.map(ion => {
    const concentration = ion.concentration + ion.coefficient * solubility;
    if (!Number.isFinite(concentration) || concentration < 0) throw new Error('The saturation concentration is outside the supported numeric range.');
    return concentration;
  }) as [number, number];
  const residualAt = (solubility: number) => logProduct(model, concentrationsAt(solubility)) - logK;
  const initialResidual = residualAt(0);
  if (initialResidual > TOLERANCE) throw new Error('The common-ion solution is already supersaturated. This dissolution-only model cannot solve precipitation.');
  if (Math.abs(initialResidual) <= TOLERANCE) return { solubility: 0, concentrations: concentrationsAt(0), logResidual: initialResidual, iterations: 0 };
  let lo = 0;
  let hi = Math.max(1e-3, ...model.ions.map(ion => ion.concentration / ion.coefficient));
  let fHi = residualAt(hi);
  for (let i = 0; fHi < 0 && i < MAX_ITERATIONS; i++) {
    hi *= 2;
    if (!Number.isFinite(hi)) throw new Error('The solubility is outside the supported numeric range.');
    fHi = residualAt(hi);
  }
  if (!(fHi >= 0)) throw new Error('Could not bracket a saturation solution.');
  let solubility = 0;
  let logResidual = Infinity;
  let iterations = 0;
  for (; iterations < MAX_ITERATIONS; iterations++) {
    solubility = lo / 2 + hi / 2;
    if (solubility === lo || solubility === hi) break;
    logResidual = residualAt(solubility);
    if (Math.abs(logResidual) <= TOLERANCE) break;
    if (logResidual < 0) lo = solubility;
    else hi = solubility;
  }
  if (!(solubility > 0) || !Number.isFinite(logResidual) || Math.abs(logResidual) > TOLERANCE) {
    throw new Error('The solubility calculation did not converge at supported numerical precision.');
  }
  const concentrations = concentrationsAt(solubility);
  const spectatorBalance = validateSpectators(model.spectators, model.activityMode);
  let charge = spectatorBalance.charge;
  let chargeScale = spectatorBalance.scale;
  model.ions.forEach((ion, index) => {
    const materialResidual = concentrations[index] - ion.concentration - ion.coefficient * solubility;
    if (Math.abs(materialResidual) > 1e-10 * Math.max(concentrations[index], ion.concentration, 1e-300)) throw new Error('The ion material-balance check failed.');
    charge += ion.charge * concentrations[index];
    chargeScale += Math.abs(ion.charge * concentrations[index]);
  });
  if (!Number.isFinite(charge) || !Number.isFinite(chargeScale)
    || (chargeScale === 0 ? charge !== 0 : Math.abs(charge / chargeScale) > TOLERANCE)) throw new Error('The final charge-balance check failed.');
  return { solubility, concentrations, logResidual, iterations: iterations + 1 };
}

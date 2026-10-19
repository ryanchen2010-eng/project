/** One aqueous acid/base family, fixed entered activities, and a 1 mol/L standard state. */
export type AcidBaseModel = 'strong-acid' | 'strong-base' | 'weak-acid' | 'weak-base' | 'buffer' | 'polyprotic';
export type ConstantInput = { value: number; notation: 'K' | 'pK' };
export type AcidBaseActivities = { mode: 'ideal' } | {
  mode: 'entered'; hydrogen: number; hydroxide: number; family: number[]; counterions: number[];
};
export type AcidBaseInput = {
  model: AcidBaseModel;
  temperatureC: number;
  kw: ConstantInput;
  activities: AcidBaseActivities;
  concentration?: number;
  constants?: ConstantInput[];
  bufferKind?: 'acid' | 'base';
  acidConcentration?: number;
  baseConcentration?: number;
  steps?: 1 | 2 | 3;
  /** Monovalent spectator cation concentration, e.g. added salt/base equivalents. */
  counterionConcentration?: number;
};
export type AcidBaseSpecies = {
  name: string; charge: number; concentration: number; coefficient: number; activity: number;
};
export type AcidBaseResult = {
  pH: number; pOH: number; hydrogen: number; hydroxide: number;
  species: AcidBaseSpecies[]; temperatureC: number; activityMode: 'ideal' | 'entered';
  chargeResidual: number; materialResidual: number; equilibriumResidual: number; iterations: number;
};
type Family = { total: number; names: string[]; charges: number[]; logKas: number[] };
type Counterion = { name: string; concentration: number; charge: number };

function finite(value: unknown, label: string): asserts value is number {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`${label} must be a finite number.`);
}
function concentration(value: unknown, label: string) {
  finite(value, label);
  if (value < 0 || value > 1e6) throw new Error(`${label} must be between 0 and 1,000,000 mol/L.`);
  return value;
}
function gamma(value: unknown, label: string) {
  finite(value, label);
  if (value < 1e-100 || value > 1e100) throw new Error(`Enter a positive ${label} between 1e-100 and 1e100.`);
  return value;
}
/** Keep constants in log space; no lookup or temperature correction is performed. */
export function constantLog10(input: ConstantInput | undefined, label = 'Constant'): number {
  if (!input || typeof input !== 'object') throw new Error(`Enter ${label}.`);
  finite(input.value, label);
  if (input.notation === 'pK') {
    if (input.value < -300 || input.value > 300) throw new Error(`${label} pK must be between −300 and 300.`);
    return -input.value;
  }
  if (input.notation !== 'K') throw new Error(`Select K or pK notation for ${label}.`);
  if (input.value < 1e-300 || input.value > 1e300) throw new Error(`${label} must be positive and between 1e-300 and 1e300.`);
  return Math.log10(input.value);
}

function defineModel(input: AcidBaseInput, logKw: number) {
  let family: Family | undefined;
  const counterions: Counterion[] = [];
  const constants = input.constants;
  const read = (count: number, label: string) => {
    if (!Array.isArray(constants) || constants.length !== count) throw new Error(`Enter all ${count} ${label} constant${count === 1 ? '' : 's'}.`);
    return constants.map((item, i) => constantLog10(item, `${label}${count > 1 ? i + 1 : ''}`));
  };
  if (input.model === 'strong-acid' || input.model === 'strong-base') {
    const amount = concentration(input.concentration, 'Analytical concentration');
    counterions.push({ name: input.model === 'strong-acid' ? 'X− (spectator)' : 'M+ (spectator)',
      concentration: amount, charge: input.model === 'strong-acid' ? -1 : 1 });
  } else if (input.model === 'weak-acid' || input.model === 'weak-base') {
    const total = concentration(input.concentration, 'Analytical concentration');
    const isBase = input.model === 'weak-base';
    const [logConstant] = read(1, isBase ? 'Kb' : 'Ka');
    family = { total, names: isBase ? ['BH+', 'B'] : ['HA', 'A−'],
      charges: isBase ? [1, 0] : [0, -1], logKas: [isBase ? logKw - logConstant : logConstant] };
  } else if (input.model === 'buffer') {
    if (input.bufferKind !== 'acid' && input.bufferKind !== 'base') throw new Error('Select an acid or base conjugate pair.');
    const acid = concentration(input.acidConcentration, 'Initial acid-form concentration');
    const base = concentration(input.baseConcentration, 'Initial base-form concentration');
    const total = acid + base;
    if (!Number.isFinite(total) || total > 1e6) throw new Error('Total family concentration is outside the supported range.');
    const isBase = input.bufferKind === 'base';
    const [logConstant] = read(1, isBase ? 'Kb' : 'Ka');
    family = { total, names: isBase ? ['BH+', 'B'] : ['HA', 'A−'],
      charges: isBase ? [1, 0] : [0, -1], logKas: [isBase ? logKw - logConstant : logConstant] };
    counterions.push({ name: isBase ? 'X− (spectator)' : 'M+ (spectator)',
      charge: isBase ? -1 : 1, concentration: isBase ? acid : base });
  } else if (input.model === 'polyprotic') {
    if (input.steps !== 1 && input.steps !== 2 && input.steps !== 3) throw new Error('Choose one to three dissociation steps.');
    const total = concentration(input.concentration, 'Total acid-family concentration');
    const counter = concentration(input.counterionConcentration, 'Spectator cation concentration');
    if (counter > input.steps * total) throw new Error('Spectator cation equivalents cannot exceed the fully neutralized family.');
    const names = input.steps === 1 ? ['HA', 'A−'] : input.steps === 2 ? ['H₂A', 'HA−', 'A²−'] : ['H₃A', 'H₂A−', 'HA²−', 'A³−'];
    family = { total, names, charges: names.map((_, i) => -i), logKas: read(input.steps, 'Ka') };
    counterions.push({ name: 'M+ (spectator)', charge: 1, concentration: counter });
  } else throw new Error('Unsupported acid–base model.');
  return { family, counterions };
}

/** Full charge + family mass balance, not a small-dissociation or Henderson–Hasselbalch approximation. */
export function calculateAcidBase(input: AcidBaseInput): AcidBaseResult {
  if (!input || typeof input !== 'object') throw new Error('Enter the acid–base inputs.');
  finite(input.temperatureC, 'Temperature');
  if (input.temperatureC <= -273.15) throw new Error('Temperature must be above absolute zero.');
  const logKw = constantLog10(input.kw, 'Kw');
  const { family, counterions } = defineModel(input, logKw);
  if (!input.activities || (input.activities.mode !== 'ideal' && input.activities.mode !== 'entered')) throw new Error('Select an activity mode.');
  const entered = input.activities.mode === 'entered' ? input.activities : undefined;
  const gammaH = entered ? gamma(entered.hydrogen, 'γ(H+)') : 1;
  const gammaOH = entered ? gamma(entered.hydroxide, 'γ(OH−)') : 1;
  if (entered && (!Array.isArray(entered.family) || entered.family.length !== (family?.names.length ?? 0)
    || !Array.isArray(entered.counterions) || entered.counterions.length !== counterions.length)) {
    throw new Error('Enter an activity coefficient for every family species and spectator ion.');
  }
  const gammaFamily = family?.names.map((name, i) => entered ? gamma(entered.family[i], `γ(${name})`) : 1) ?? [];
  const gammaCounter = counterions.map((ion, i) => entered ? gamma(entered.counterions[i], `γ(${ion.name})`) : 1);
  const logGammaH = Math.log10(gammaH);
  const logGammaOH = Math.log10(gammaOH);
  // Both water species must remain representable; use no fabricated concentration floors.
  let lower = Math.max(-300, logKw - logGammaH - logGammaOH - 300);
  let upper = Math.min(300, logKw - logGammaH - logGammaOH + 300);
  if (!(lower < upper)) throw new Error('These constants and coefficients are outside the solver’s numeric range.');
  function state(logH: number) {
    const h = 10 ** logH;
    const oh = 10 ** (logKw - logGammaH - logGammaOH - logH);
    const amounts: number[] = [];
    if (family) {
      const weights = [0];
      for (let i = 0; i < family.logKas.length; i++) weights.push(weights[i] + family.logKas[i]
        + Math.log10(gammaFamily[i]) - logGammaH - logH - Math.log10(gammaFamily[i + 1]));
      const maximum = Math.max(...weights);
      const scaled = weights.map((weight) => 10 ** (weight - maximum));
      const sum = scaled.reduce((a, b) => a + b, 0);
      amounts.push(...scaled.map((value) => family.total * value / sum));
    }
    let positive = h;
    let negative = oh;
    family?.charges.forEach((charge, i) => {
      if (charge > 0) positive += charge * amounts[i];
      else negative -= charge * amounts[i];
    });
    counterions.forEach((ion) => {
      if (ion.charge > 0) positive += ion.charge * ion.concentration;
      else negative -= ion.charge * ion.concentration;
    });
    const residual = (positive - negative) / Math.max(positive, negative);
    if (![h, oh, positive, negative, residual].every(Number.isFinite) || h <= 0 || oh <= 0) throw new Error('The numeric range of these inputs is unsupported.');
    return { h, oh, amounts, residual };
  }
  if (state(lower).residual > 0 || state(upper).residual < 0) throw new Error('No positive charge-balanced solution was bracketed.');
  let logH = (lower + upper) / 2;
  let final = state(logH);
  let iterations = 0;
  for (; iterations < 400; iterations++) {
    logH = (lower + upper) / 2;
    final = state(logH);
    if (Math.abs(final.residual) <= 1e-12) break;
    if (final.residual > 0) upper = logH;
    else lower = logH;
    if (upper - lower <= Number.EPSILON * Math.max(1, Math.abs(logH))) break;
  }
  if (iterations >= 400 || Math.abs(final.residual) > 1e-10) throw new Error('The charge-balance calculation did not converge.');
  const species: AcidBaseSpecies[] = [];
  const add = (name: string, charge: number, amount: number, coefficient: number) => {
    const activity = amount * coefficient; // c° = 1 mol/L
    if (!Number.isFinite(activity) || (amount > 0 && activity <= 0)) throw new Error('A species activity is outside the numeric range.');
    species.push({ name, charge, concentration: amount, coefficient, activity });
  };
  add('H+', 1, final.h, gammaH);
  add('OH−', -1, final.oh, gammaOH);
  let materialResidual = 0;
  let equilibriumResidual = Math.abs(Math.log10(final.h) + logGammaH + Math.log10(final.oh) + logGammaOH - logKw);
  if (family) {
    const sum = final.amounts.reduce((a, b) => a + b, 0);
    materialResidual = family.total === 0 ? sum : Math.abs(sum - family.total) / family.total;
    family.names.forEach((name, i) => add(name, family.charges[i], final.amounts[i], gammaFamily[i]));
    if (family.total > 0) {
      if (final.amounts.some((amount) => amount <= 0 || !Number.isFinite(amount))) throw new Error('A family species is below the supported numeric range; no approximate result is shown.');
      for (let i = 0; i < family.logKas.length; i++) {
        const logQ = logH + logGammaH + Math.log10(final.amounts[i + 1]) + Math.log10(gammaFamily[i + 1])
          - Math.log10(final.amounts[i]) - Math.log10(gammaFamily[i]);
        equilibriumResidual = Math.max(equilibriumResidual, Math.abs(logQ - family.logKas[i]));
      }
    }
  }
  counterions.forEach((ion, i) => add(ion.name, ion.charge, ion.concentration, gammaCounter[i]));
  if (materialResidual > 1e-10 || equilibriumResidual > 1e-8) throw new Error('The mass or equilibrium balance check failed.');
  const pH = -(logH + logGammaH);
  const pOH = -(Math.log10(final.oh) + logGammaOH);
  if (![pH, pOH].every(Number.isFinite)) throw new Error('A finite pH result could not be calculated.');
  return { pH, pOH, hydrogen: final.h, hydroxide: final.oh, species, temperatureC: input.temperatureC,
    activityMode: input.activities.mode, chargeResidual: Math.abs(final.residual), materialResidual, equilibriumResidual, iterations: iterations + 1 };
}

export type AmountUnit = 'g' | 'mg' | 'mol' | 'mmol';
export type Quantity = { value: number; unit: AmountUnit };
export type StoichiometricSpecies = { name: string; formula: string; molarMass: number; coefficient: number };
export type CalculationContext = {
  version: 1; assertionLevel: 'conditional-net'; pathway: string; label: string; conditionStatus: string;
  conditions: Record<string, string>; missingRequiredSettings: string[]; unknownConditions: string[];
  canGenerate3D: boolean; assumptions: string[]; warning: string;
  namedConditionProfile?: Record<string, unknown>;
};
export type ReactionStoichiometry = {
  balanced: boolean;
  reactants: (StoichiometricSpecies & { inputSlot: 0 | 1 })[];
  product: StoichiometricSpecies;
  excludedInputs: { inputSlot: 0 | 1; name: string; reason: string }[];
  notes: string[];
  context?: CalculationContext;
};

/** Copy external confidence metadata without trusting arbitrary values/HTML. */
export function copyCalculationContext(value: unknown): CalculationContext {
  if (!value || typeof value !== 'object') throw new Error('Calculation context is invalid.');
  const item = value as Record<string, unknown>;
  const text = (v: unknown, limit = 1000): v is string => typeof v === 'string' && Boolean(v.trim()) && v.length <= limit;
  const strings = (v: unknown): v is string[] => Array.isArray(v) && v.length <= 30 && v.every((s) => text(s, 5000));
  if (item.version !== 1 || item.assertionLevel !== 'conditional-net' || !text(item.pathway, 200)
    || !text(item.label) || !text(item.conditionStatus, 100) || !text(item.warning)
    || typeof item.canGenerate3D !== 'boolean' || !strings(item.missingRequiredSettings)
    || !strings(item.unknownConditions) || !strings(item.assumptions)
    || !item.conditions || typeof item.conditions !== 'object' || Array.isArray(item.conditions)) {
    throw new Error('Calculation context is invalid.');
  }
  const conditions = Object.entries(item.conditions);
  if (conditions.length > 12 || conditions.some(([key, v]) => !/^[A-Za-z][A-Za-z0-9]*$/.test(key)
    || key.length > 50 || typeof v !== 'string' || v.length > 200)) throw new Error('Calculation context is invalid.');
  let named: Record<string, unknown> | undefined;
  if (item.namedConditionProfile !== undefined) {
    const raw = item.namedConditionProfile as Record<string, unknown>;
    if (!raw || typeof raw !== 'object' || Array.isArray(raw) || raw.version !== 1
      || !['explicit', 'legacy-inferred'].includes(String(raw.selection))
      || !['qualified', 'unresolved', 'rejected'].includes(String(raw.status))
      || JSON.stringify(raw).length > 30000) throw new Error('Named calculation context is invalid.');
    const ref = raw.reference as Record<string, unknown>;
    const descriptor = raw.descriptor as Record<string, unknown> | null;
    if (!ref || typeof ref.id !== 'string' || typeof ref.version !== 'string'
      || (raw.status !== 'rejected' && (!descriptor || descriptor.version !== 1
        || descriptor.id !== ref.id || String(descriptor.profileVersion) !== ref.version
        || descriptor.pathway !== item.pathway || !Array.isArray(descriptor.facts)
        || !Array.isArray(descriptor.assumptions) || !Array.isArray(descriptor.unknowns)))) {
      throw new Error('Named calculation context is invalid.');
    }
    if (raw.selection === 'explicit' && ((item.conditions as Record<string, unknown>).conditionProfileId !== ref.id
      || (item.conditions as Record<string, unknown>).conditionProfileVersion !== ref.version)) {
      throw new Error('Named calculation context conflicts with its inputs.');
    }
    named = JSON.parse(JSON.stringify(raw)) as Record<string, unknown>; // Detached facts, never authorization.
  }
  return { version: 1, assertionLevel: 'conditional-net', pathway: item.pathway, label: item.label,
    conditionStatus: item.conditionStatus, conditions: Object.fromEntries(conditions),
    missingRequiredSettings: [...item.missingRequiredSettings], unknownConditions: [...item.unknownConditions],
    canGenerate3D: item.canGenerate3D, assumptions: [...item.assumptions], warning: item.warning,
    ...(named ? { namedConditionProfile: named } : {}) };
}

function positive(value: number, label: string): void {
  if (!Number.isFinite(value) || value <= 0) throw new Error(`${label} must be a positive finite number.`);
}

function finite(value: number): number {
  if (!Number.isFinite(value)) throw new Error('These amounts are too large to calculate reliably.');
  return value;
}

export function validateStoichiometry(data: ReactionStoichiometry): void {
  if (!data || data.balanced !== true) throw new Error('A verified balanced equation is required.');
  if (data.context !== undefined) copyCalculationContext(data.context);
  if (!Array.isArray(data.reactants) || !data.reactants.length || data.reactants.length > 2) {
    throw new Error('The consumed reactants are unavailable.');
  }
  const slots = new Set<number>();
  for (const species of [...data.reactants, data.product]) {
    if (!species || typeof species.name !== 'string' || !species.name.trim()
      || typeof species.formula !== 'string' || !species.formula.trim()) throw new Error('Compound information is incomplete.');
    positive(species.molarMass, 'Molar mass');
    if (!Number.isSafeInteger(species.coefficient) || species.coefficient <= 0) {
      throw new Error('Equation coefficients must be positive integers.');
    }
  }
  for (const reactant of data.reactants) {
    if ((reactant.inputSlot !== 0 && reactant.inputSlot !== 1) || slots.has(reactant.inputSlot)) {
      throw new Error('The reactant input correspondence is invalid.');
    }
    slots.add(reactant.inputSlot);
  }
}

/** Quantities refer to pure compound/reagent, never the mass of a solution. */
export function toMoles(quantity: Quantity, molarMass: number): number {
  positive(molarMass, 'Molar mass');
  if (!quantity || !Number.isFinite(quantity.value) || quantity.value < 0) {
    throw new Error('Enter a finite amount of zero or more.');
  }
  let moles: number;
  switch (quantity.unit) {
    case 'g': moles = quantity.value / molarMass; break;
    case 'mg': moles = quantity.value / 1000 / molarMass; break;
    case 'mol': moles = quantity.value; break;
    case 'mmol': moles = quantity.value / 1000; break;
    default: throw new Error('Choose g, mg, mol, or mmol.');
  }
  finite(moles);
  if (quantity.value > 0 && moles === 0) throw new Error('This amount is too small to calculate reliably.');
  return moles;
}

export function calculateReaction(data: ReactionStoichiometry, amounts: Partial<Record<0 | 1, Quantity>>) {
  validateStoichiometry(data);
  const available = data.reactants.map((reactant) => {
    const quantity = amounts?.[reactant.inputSlot];
    if (!quantity) throw new Error(`Enter an amount for ${reactant.name}.`);
    const moles = toMoles(quantity, reactant.molarMass);
    // Dividing by the equation coefficient gives the possible reaction extent.
    return { reactant, moles, extent: moles / reactant.coefficient };
  });
  const extent = Math.min(...available.map((item) => item.extent));
  const productMoles = finite(extent * data.product.coefficient);
  const limitingInputs = available.filter((item) => item.extent === extent
    || Math.abs(item.extent - extent) <= Math.max(Math.abs(extent), Math.abs(item.extent)) * 1e-9)
    .map((item) => item.reactant.inputSlot);
  return {
    extent,
    product: { moles: productMoles, grams: finite(productMoles * data.product.molarMass) },
    limitingInputs,
    reactants: available.map(({ reactant, moles }) => {
      const consumedMoles = Math.min(moles, finite(extent * reactant.coefficient));
      const remainingMoles = Math.max(0, moles - consumedMoles);
      return { inputSlot: reactant.inputSlot, name: reactant.name, availableMoles: moles, consumedMoles,
        remainingMoles, remainingGrams: finite(remainingMoles * reactant.molarMass) };
    }),
  };
}

/** Stoichiometric minimum at 100% conversion, not a practical synthesis recipe. */
export function calculateRequiredAmounts(data: ReactionStoichiometry, target: Quantity) {
  validateStoichiometry(data);
  const moles = toMoles(target, data.product.molarMass);
  positive(moles, 'Target product amount');
  const extent = moles / data.product.coefficient;
  return {
    product: { moles, grams: finite(moles * data.product.molarMass) },
    reactants: data.reactants.map((reactant) => {
      const requiredMoles = finite(extent * reactant.coefficient);
      return { inputSlot: reactant.inputSlot, name: reactant.name, moles: requiredMoles,
        grams: finite(requiredMoles * reactant.molarMass) };
    }),
  };
}

export type VolumeUnit = 'L' | 'mL' | 'µL';
export type ConcentrationUnit = 'mol/L' | 'mmol/L' | 'µmol/L';
export type SoluteAmountUnit = 'g' | 'mg' | 'mol' | 'mmol';

export type Volume = { value: number; unit: VolumeUnit };
export type Concentration = { value: number; unit: ConcentrationUnit };
export type SoluteAmount = { value: number; unit: SoluteAmountUnit };

export type MolarityResult = {
  moles: number;
  litres: number;
  molarity: number;
  grams?: number;
};

export type SoluteMassResult = {
  moles: number;
  grams: number;
  litres: number;
  molarity: number;
};

export type DilutionResult = {
  stockLitres: number;
  finalLitres: number;
  stockMolarity: number;
  targetMolarity: number;
  dilutionFactor: number;
};

function positive(value: number, label: string): number {
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${label} must be a positive finite number.`);
  }
  return value;
}

/** Reject overflow and values that underflow to zero instead of displaying a false result. */
function calculated(value: number): number {
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error('These values are too large or too small to calculate reliably.');
  }
  return value;
}

function toLitres(volume: Volume): number {
  const value = positive(volume?.value, 'Solution volume');
  switch (volume.unit) {
    case 'L': return value;
    case 'mL': return calculated(value / 1000);
    case 'µL': return calculated(value / 1_000_000);
    default: throw new Error('Choose L, mL, or µL for volume.');
  }
}

function toMolarity(concentration: Concentration, label: string): number {
  const value = positive(concentration?.value, label);
  switch (concentration.unit) {
    case 'mol/L': return value;
    case 'mmol/L': return calculated(value / 1000);
    case 'µmol/L': return calculated(value / 1_000_000);
    default: throw new Error('Choose mol/L, mmol/L, or µmol/L for concentration.');
  }
}

/** Volume is the final total solution volume, not the volume of solvent added. */
export function calculateMolarity(input: {
  amount: SoluteAmount;
  volume: Volume;
  molarMass?: number;
}): MolarityResult {
  const value = positive(input?.amount?.value, 'Solute amount');
  const litres = toLitres(input.volume);
  const molarMass = input.molarMass === undefined ? undefined : positive(input.molarMass, 'Molar mass');
  let moles: number;
  let grams: number | undefined;

  switch (input.amount.unit) {
    case 'g':
    case 'mg': {
      if (molarMass === undefined) throw new Error('Enter molar mass in g/mol to convert a solute mass.');
      grams = input.amount.unit === 'g' ? value : calculated(value / 1000);
      moles = calculated(grams / molarMass);
      break;
    }
    case 'mol': moles = value; break;
    case 'mmol': moles = calculated(value / 1000); break;
    default: throw new Error('Choose g, mg, mol, or mmol for solute amount.');
  }

  const molarity = calculated(moles / litres);
  if (grams === undefined && molarMass !== undefined) grams = calculated(moles * molarMass);
  return { moles, litres, molarity, ...(grams === undefined ? {} : { grams }) };
}

/** Pure solute mass for the specified final total solution volume; no purity correction. */
export function calculateSoluteMass(input: {
  concentration: Concentration;
  volume: Volume;
  molarMass: number;
}): SoluteMassResult {
  const molarMass = positive(input?.molarMass, 'Molar mass');
  const molarity = toMolarity(input.concentration, 'Target concentration');
  const litres = toLitres(input.volume);
  const moles = calculated(molarity * litres);
  const grams = calculated(moles * molarMass);
  return { moles, grams, litres, molarity };
}

/**
 * C₁V₁ = C₂V₂ for the same solute without reaction or solute loss.
 * stockLitres is the aliquot; finalLitres is the final total volume.
 * No exact solvent-addition volume is inferred because volumes need not be additive.
 */
export function calculateDilution(input: {
  stock: Concentration;
  target: Concentration;
  finalVolume: Volume;
}): DilutionResult {
  const stockMolarity = toMolarity(input?.stock, 'Stock concentration');
  const targetMolarity = toMolarity(input.target, 'Target concentration');
  const finalLitres = toLitres(input.finalVolume);
  if (targetMolarity > stockMolarity) {
    throw new Error('Target concentration cannot exceed the stock concentration for dilution.');
  }
  const dilutionFactor = calculated(stockMolarity / targetMolarity);
  const stockLitres = calculated(finalLitres / dilutionFactor);
  return { stockLitres, finalLitres, stockMolarity, targetMolarity, dilutionFactor };
}

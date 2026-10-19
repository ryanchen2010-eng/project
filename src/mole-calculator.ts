/** SI-defined Avogadro constant; counts the specified entity, not its constituent atoms. */
export const AVOGADRO_CONSTANT = 6.02214076e23;
export type EntityKind = 'molecules' | 'atoms' | 'formula-units';
export type MoleInputUnit = 'kg' | 'g' | 'mg' | 'µg' | 'mol' | 'mmol' | 'µmol' | 'particles';
export type MoleConversionInput = { value: number; unit: MoleInputUnit; molarMass?: number; entityKind: EntityKind };
export type MoleConversion = { moles: number; particles: number; grams?: number; entityKind: EntityKind };
const MASS_FACTORS = { kg: 1000, g: 1, mg: 1e-3, 'µg': 1e-6 } as const;
const MOLE_FACTORS = { mol: 1, mmol: 1e-3, 'µmol': 1e-6 } as const;

function representable(value: number, positiveExpected: boolean) {
  if (!Number.isFinite(value) || value < 0 || (positiveExpected && value === 0)) {
    throw new Error('The amount is outside the supported numerical range.');
  }
  return value;
}

export function convertMoles(input: MoleConversionInput): MoleConversion {
  if (!input || typeof input !== 'object' || typeof input.value !== 'number' || !Number.isFinite(input.value) || input.value < 0) {
    throw new Error('Enter a finite amount of zero or more.');
  }
  if (!['molecules', 'atoms', 'formula-units'].includes(input.entityKind)) throw new Error('Choose the entity being counted.');
  if (input.molarMass !== undefined && (typeof input.molarMass !== 'number' || !Number.isFinite(input.molarMass) || input.molarMass <= 0)) {
    throw new Error('Enter a positive molar mass in g/mol.');
  }
  const positive = input.value > 0;
  let moles: number;
  if (Object.hasOwn(MASS_FACTORS, input.unit)) {
    if (input.molarMass === undefined) throw new Error('Mass conversion needs the exact entity’s molar mass.');
    const grams = representable(input.value * MASS_FACTORS[input.unit as keyof typeof MASS_FACTORS], positive);
    moles = representable(grams / input.molarMass, positive);
  } else if (Object.hasOwn(MOLE_FACTORS, input.unit)) {
    moles = representable(input.value * MOLE_FACTORS[input.unit as keyof typeof MOLE_FACTORS], positive);
  } else if (input.unit === 'particles') {
    moles = representable(input.value / AVOGADRO_CONSTANT, positive);
  } else throw new Error('Choose a supported amount unit.');
  const particles = representable(moles * AVOGADRO_CONSTANT, positive);
  const grams = input.molarMass === undefined ? undefined : representable(moles * input.molarMass, positive);
  return { moles, particles, ...(grams === undefined ? {} : { grams }), entityKind: input.entityKind };
}

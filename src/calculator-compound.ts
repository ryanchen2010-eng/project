import type { Molecule } from './molecules';
import type { Reactant } from './reactant-entry';
import type { SolutionCompound } from './solution-calculator-panel';
import type { EntityKind } from './mole-calculator';
import { parseMolarMass } from './solution-compound';

export const CALCULATOR_TRANSFER_KEY = 'molecule-playground.calculator-compound.v1';
export type CalculatorCompound = SolutionCompound & {
  entityKind: EntityKind;
  cid?: number;
  structure?: string;
};

/** Keep exact identity and the full salt/hydrate mass; never match a formula to another compound. */
export function calculatorCompoundFromMolecule(molecule: Molecule, ionic: boolean): CalculatorCompound {
  // Only an exact one-atom bracketed SMILES is atomic. Formula-only guesses are unsafe.
  const monatomic = /^\[(?:\d+)?[A-Z][a-z]?(?:[+-]\d*)?\]$/.test(molecule.structureForm?.trim() ?? '');
  return { id: molecule.id, name: molecule.name, formula: molecule.formula,
    molarMass: parseMolarMass(molecule.properties.mass), entityKind: monatomic ? 'atoms' : ionic ? 'formula-units' : 'molecules',
    cid: molecule.cid, structure: molecule.structureForm };
}

/** Reaction inputs transfer their exact structure, never a mass borrowed by formula. */
export function calculatorCompoundFromReactant(reactant: Reactant, records: Molecule[]): CalculatorCompound {
  const reviewed = records.find((record) => record.id === reactant.id && record.structureForm === reactant.smiles);
  if (reviewed) return calculatorCompoundFromMolecule(reviewed, reviewed.ionicAssembly === true || reviewed.category === 'Ionic compound');
  const monatomic = /^\[(?:\d+)?[A-Z][a-z]?(?:[+-]\d*)?\]$/.test(reactant.smiles.trim());
  return { id: reactant.id, name: reactant.name, formula: reactant.formula, structure: reactant.smiles,
    entityKind: monatomic ? 'atoms' : 'molecules' };
}

export function encodeCalculatorTransfer(compound: CalculatorCompound): string {
  return JSON.stringify({ version: 1, compound });
}

/** Storage is untrusted: validate shape, bound text, and render all labels as text. */
export function decodeCalculatorTransfer(raw: string | null): CalculatorCompound | undefined {
  if (!raw || raw.length > 16_000) return undefined;
  try {
    const data = JSON.parse(raw);
    const c = data?.compound;
    if (data?.version !== 1 || !c || typeof c !== 'object' || Array.isArray(c)) return undefined;
    for (const key of ['id', 'name'] as const) if (typeof c[key] !== 'string' || !c[key].trim() || c[key].length > 200) return undefined;
    if (!['molecules', 'atoms', 'formula-units'].includes(c.entityKind)) return undefined;
    if (c.formula !== undefined && (typeof c.formula !== 'string' || c.formula.length > 100)) return undefined;
    if (c.structure !== undefined && (typeof c.structure !== 'string' || c.structure.length > 10_000)) return undefined;
    if (c.cid !== undefined && (!Number.isSafeInteger(c.cid) || c.cid < 1)) return undefined;
    if (c.molarMass !== undefined && (typeof c.molarMass !== 'number' || !Number.isFinite(c.molarMass) || c.molarMass <= 0)) return undefined;
    return { id: c.id, name: c.name, formula: c.formula, molarMass: c.molarMass,
      entityKind: c.entityKind, cid: c.cid, structure: c.structure };
  } catch { return undefined; }
}
